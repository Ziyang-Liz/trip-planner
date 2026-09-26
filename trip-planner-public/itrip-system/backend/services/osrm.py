from typing import List, Tuple
from .utils import http_client, http_timeout

Coord = Tuple[float, float]  # (lat, lon)

def _fmt(c: Coord) -> str:
    lat, lon = c
    return f"{lon},{lat}"  # OSRM expects lon,lat

async def route(coords: List[Coord]):
    if len(coords) < 2:
        return 0.0, 0.0, []
    path = ";".join(_fmt(c) for c in coords)
    url = f"https://router.project-osrm.org/route/v1/driving/{path}?overview=simplified&geometries=geojson"
    async with http_client() as client:
        r = await client.get(url, timeout=http_timeout(10))
        r.raise_for_status()
        js = r.json()
        best = js["routes"][0]
        dist_km = best["distance"] / 1000.0
        dur_min = best["duration"] / 60.0
        geo = best["geometry"]["coordinates"]  # [[lon,lat], ...]
        waypoints = [(p[1], p[0]) for p in geo[::10]]
        return round(dist_km, 2), round(dur_min, 1), waypoints


async def travel_matrix(coords: List[Coord]):
    """Directed driving durations (seconds) and distances (metres)."""
    path = ";".join(_fmt(c) for c in coords)
    async with http_client() as client:
        response = await client.get(
            f"https://router.project-osrm.org/table/v1/driving/{path}",
            params={"annotations": "duration,distance"}, timeout=http_timeout(8),
        )
        response.raise_for_status()
        return response.json()
