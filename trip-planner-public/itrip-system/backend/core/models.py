from pydantic import BaseModel
from typing import List, Tuple, Optional

Coord = Tuple[float, float]

class POI(BaseModel):
    name: str
    lat: float
    lon: float
    osm_id: Optional[int] = None
    category: Optional[str] = None

class PlanResponse(BaseModel):
    origin: str
    destination: str
    origin_coord: Coord
    destination_coord: Coord
    pois: List[POI]
    route_distance_km: float
    route_duration_min: float
    waypoints: List[Coord]
