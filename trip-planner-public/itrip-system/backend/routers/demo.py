# backend/routers/demo.py
from __future__ import annotations

from fastapi import APIRouter, Query, Depends
from typing import List, Tuple, Dict, Any
import asyncio
import time
import hashlib
import httpx

# Import models and database session
from core.models import PlanResponse, POI, Coord
from core.db import get_db
from core.models_db import TripHistory
from sqlalchemy.orm import Session

router = APIRouter(prefix="/demo", tags=["Demo"])


_CACHE: Dict[str, Tuple[float, Any]] = {}
_CACHE_TTL = 600.0  # seconds

def _cache_key(*parts: str) -> str:
    return hashlib.md5("|".join(parts).encode()).hexdigest()

def get_cache(key: str):
    hit = _CACHE.get(key)
    if not hit:
        return None
    ts, val = hit
    if time.time() - ts > _CACHE_TTL:
        _CACHE.pop(key, None)
        return None
    return val

def set_cache(key: str, val: Any):
    _CACHE[key] = (time.time(), val)

# OpenStreetMap API Integrations

_HEADERS = {"User-Agent": "itrip-thesis-demo/1.0 (student project)"}

async def geocode(city: str) -> Tuple[float, float]:
    
    url = "https://nominatim.openstreetmap.org/search"
    params = {"q": city, "format": "json", "limit": 1}
    async with httpx.AsyncClient(headers=_HEADERS, timeout=20) as client:
        r = await client.get(url, params=params)
        r.raise_for_status()
        data = r.json()
        if not data:
            raise ValueError(f"Geocoding failed for: {city}")
        lat = float(data[0]["lat"])
        lon = float(data[0]["lon"])
        return (lat, lon)

async def fetch_pois(lat: float, lon: float, limit: int = 4) -> List[POI]:
    
    radius = 5000  # meters
    query = f"""
    [out:json][timeout:25];
    (
      node["tourism"="attraction"](around:{radius},{lat},{lon});
      node["amenity"="place_of_worship"](around:{radius},{lat},{lon});
      node["historic"](around:{radius},{lat},{lon});
    );
    out center {limit};
    """

    url = "https://overpass-api.de/api/interpreter"
    async with httpx.AsyncClient(headers=_HEADERS, timeout=40) as client:
        r = await client.post(url, data={"data": query})
        r.raise_for_status()
        data = r.json()

    elements = data.get("elements", [])[:limit]
    pois: List[POI] = []
    for el in elements:
        name = el.get("tags", {}).get("name") or "POI"
        latp = el.get("lat") or (el.get("center") or {}).get("lat")
        lonp = el.get("lon") or (el.get("center") or {}).get("lon")
        if latp is None or lonp is None:
            continue
        pois.append(
            POI(
                name=name,
                lat=float(latp),
                lon=float(lonp),
                osm_id=int(el.get("id", 0)),
                category=el.get("tags", {}).get("tourism")
                or el.get("tags", {}).get("amenity")
                or el.get("tags", {}).get("historic")
                or "poi",
            )
        )
    return pois[:limit]

async def osrm_route(coords: List[Coord]) -> Tuple[float, float, List[Coord]]:
    
    if len(coords) < 2:
        return 0.0, 0.0, coords

    # OSRM uses "lon,lat" format
    coord_str = ";".join([f"{c[1]},{c[0]}" for c in coords])
    url = f"http://router.project-osrm.org/route/v1/driving/{coord_str}"
    params = {"overview": "full", "geometries": "geojson"}

    async with httpx.AsyncClient(headers=_HEADERS, timeout=40) as client:
        r = await client.get(url, params=params)
        r.raise_for_status()
        data = r.json()

    routes = data.get("routes") or []
    if not routes:
        return 0.0, 0.0, coords

    route = routes[0]
    dist_km = route["distance"] / 1000.0
    dur_min = route["duration"] / 60.0
    line = route.get("geometry", {}).get("coordinates") or []
    path: List[Coord] = [(float(ll[1]), float(ll[0])) for ll in line]
    return dist_km, dur_min, path


def nearest_order(start: Coord, poi_coords: List[Coord]) -> List[Coord]:
    if not poi_coords:
        return []
    remaining = poi_coords[:]
    cur = start
    ordered: List[Coord] = []
    while remaining:
        nxt = min(
            remaining,
            key=lambda p: (p[0] - cur[0]) ** 2 + (p[1] - cur[1]) ** 2,
        )
        ordered.append(nxt)
        remaining.remove(nxt)
        cur = nxt
    return ordered


# Endpoint 1: Generate Trip Plan

@router.get("/plan", response_model=PlanResponse)
async def generate_plan(
    origin: str = Query(..., description="Origin city name"),
    destination: str = Query(..., description="Destination city name"),
    limit: int = Query(4, ge=0, le=8, description="Number of POIs (0-8)"),
    db: Session = Depends(get_db),
):
    key = _cache_key("plan", origin, destination, str(limit))
    cached = get_cache(key)
    if cached:
        return cached

    # 1. Concurrent geocoding
    (o_lat, o_lon), (d_lat, d_lon) = await asyncio.gather(
        geocode(origin), geocode(destination)
    )

    # 2. Fetch POIs around destination
    pois_raw = await fetch_pois(d_lat, d_lon, limit=limit)
    poi_coords: List[Coord] = [(p.lat, p.lon) for p in pois_raw]

    # 3. Determine optimal visiting order (nearest-neighbor heuristic)
    ordered = nearest_order((o_lat, o_lon), poi_coords)

    # 4. Call OSRM to get route data
    coords_for_route: List[Coord] = [(o_lat, o_lon)] + ordered + [(d_lat, d_lon)]
    dist_km, dur_min, waypoints = await osrm_route(coords_for_route)

    # 5. Build API response
    resp = PlanResponse(
        origin=origin,
        destination=destination,
        origin_coord=(o_lat, o_lon),
        destination_coord=(d_lat, d_lon),
        pois=pois_raw,
        route_distance_km=round(dist_km, 2),
        route_duration_min=round(dur_min, 1),
        waypoints=waypoints,
    )

    # 6. Store cache
    set_cache(key, resp)

    # 7. Save to database (optional, ignore on error)
    try:
        row = TripHistory(
            origin=origin,
            destination=destination,
            poi_limit=limit,
            route_distance_km=resp.route_distance_km,
            route_duration_min=resp.route_duration_min,
            plan_json=resp.model_dump(mode="json"),
        )
        db.add(row)
        db.commit()
    except Exception:
        db.rollback()

    return resp


# Endpoint 2: Recent Trip History

@router.get("/history")
def recent_history(
    limit: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db),
):
    q = (
        db.query(TripHistory)
        .order_by(TripHistory.id.desc())
        .limit(limit)
        .all()
    )
    return [
        {
            "id": r.id,
            "created_at": r.created_at,
            "origin": r.origin,
            "destination": r.destination,
            "poi_limit": r.poi_limit,
            "route_distance_km": r.route_distance_km,
            "route_duration_min": r.route_duration_min,
        }
        for r in q
    ]
