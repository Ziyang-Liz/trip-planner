"""One asynchronous OSRM matrix request, reusing existing HTTP and DB cache."""

import asyncio
import math
from services.api_cache_service import get_valid_cache, make_cache_key, save_cache
from services.osrm import travel_matrix
from core.cache import get_cache, set_cache


def valid_matrix(data, size):
    if not isinstance(data, dict):
        return False
    for key in ("durations", "distances"):
        rows = data.get(key)
        if not isinstance(rows, list) or len(rows) != size:
            return False
        for row in rows:
            if not isinstance(row, list) or len(row) != size:
                return False
            if any(v is not None and (not isinstance(v, (int, float)) or not math.isfinite(v) or v < 0) for v in row):
                return False
    return True


async def fetch_travel_data(request):
    places = {a.place.id: a.place for a in request.activities}
    places.update({p.id: p for p in request.candidates})
    locations = {"@current": request.current_location}
    locations.update({"place:" + key: p.location for key, p in places.items() if p.location is not None})
    keys = sorted(locations)
    coords = [(locations[k].lat, locations[k].lon) for k in keys]
    params = {"coords": coords, "profile": "driving", "version": 1}
    key = make_cache_key("replan_matrix", params)
    data = get_cache(key)
    source = "memory_cache"
    if not valid_matrix(data, len(keys)):
        data = await asyncio.to_thread(get_valid_cache, "replan_matrix", params)
        source = "postgres_cache"
    cache_write = "not_needed"
    if not valid_matrix(data, len(keys)):
        try:
            data = await travel_matrix(coords)
            if data.get("code") != "Ok" or not valid_matrix(data, len(keys)):
                raise ValueError("invalid OSRM matrix")
            data = {name: data[name] for name in ("durations", "distances")}
            source = "osrm"
            saved = await asyncio.to_thread(save_cache, "replan_matrix", params, data, 15)
            cache_write = "saved" if saved else "unavailable"
        except Exception:
            # An explicit assumption, never represented as measured road travel.
            data = None
            source = "estimated_straight_line"
            cache_write = "not_cached"
    if data is not None:
        set_cache(key, data)
    legs = {}
    for i, a in enumerate(keys):
        for j, b in enumerate(keys):
            if data is not None:
                seconds, metres = data["durations"][i][j], data["distances"][i][j]
                legs[(a, b)] = {
                    "minutes": None if seconds is None else seconds / 60,
                    "distance_km": None if metres is None else metres / 1000,
                    "source": source, "verified": False,
                }
            else:
                lat1, lon1, lat2, lon2 = map(math.radians, (*coords[i], *coords[j]))
                h = math.sin((lat2-lat1)/2)**2 + math.cos(lat1)*math.cos(lat2)*math.sin((lon2-lon1)/2)**2
                km = 6371 * 2 * math.asin(min(1, math.sqrt(h)))
                legs[(a, b)] = {
                    "minutes": km / 25 * 60, "distance_km": km,
                    "source": source, "verified": False,
                }
    return legs, {"travel": source, "cache_write": cache_write, "pois": "original_candidate_pool"}
