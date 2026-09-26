# backend/services/overpass.py
import os, httpx, random
from .utils import http_client, http_timeout

USER_AGENT = os.getenv("USER_AGENT", "TripPlanner-Demo/1.0 (demo@example.com)")

# ① 放宽过滤（景点/博物馆/观景点/画廊/公园/广场/动物园/水族馆等）
OVERPASS_FILTER = """
  node["tourism"~"attraction|museum|viewpoint|gallery|zoo|aquarium"];
  node["amenity"~"park|arts_centre|theatre|fountain|place_of_worship"];
  node["leisure"~"park|garden"];
"""

def _bbox_from_center(lat: float, lon: float, km: float = 15.0):  # ② 半径从 8km 提到 15km
    d = km / 111.0
    return (lat - d, lon - d, lat + d, lon + d)

# ③ 多个 Overpass 端点，随机挑一个，分摊负载
OVERPASS_ENDPOINTS = [
    "https://overpass-api.de/api/interpreter",
    "https://overpass.openstreetmap.ru/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
]

async def fetch_pois(lat: float, lon: float, limit: int = 6):
    south, west, north, east = _bbox_from_center(lat, lon, km=15.0)
    query = f"""
    [out:json][timeout:25];
    (
      {OVERPASS_FILTER}({south},{west},{north},{east});
    );
    out center {max(limit * 4, limit)};   // 多取一些，后面再截断
    """

    headers = {"User-Agent": USER_AGENT}
    pois = []

    async with http_client() as client:
        # ④ 轮询多个端点，直到一个成功为止
        for base in random.sample(OVERPASS_ENDPOINTS, k=len(OVERPASS_ENDPOINTS)):
            try:
                r = await client.post(base, data=query, headers=headers, timeout=http_timeout(12))
                r.raise_for_status()
                data = r.json()
                for el in data.get("elements", []):
                    tags = el.get("tags", {})
                    name = tags.get("name") or tags.get("name:en")
                    if not name:  # 没名字的就算了
                        continue
                    lat0 = el.get("lat") or el.get("center", {}).get("lat")
                    lon0 = el.get("lon") or el.get("center", {}).get("lon")
                    if lat0 is None or lon0 is None:
                        continue
                    pois.append({
                        "name": name,
                        "lat": lat0,
                        "lon": lon0,
                        "osm_id": el.get("id"),
                        "category": tags.get("tourism") or tags.get("amenity") or tags.get("leisure"),
                    })
                break
            except Exception:
                continue

    # ⑤ 截断 + 如果结果太少，做一个“演示兜底”
    if len(pois) >= limit:
        pois = pois[:limit]
    if not pois:
        # fallback：给一些知名地标（仅演示，保证有东西可画）
        pois = _fallback_landmarks_near(lat, lon, limit)

    return pois

def _fallback_landmarks_near(lat: float, lon: float, limit: int):
    # 简单兜底：靠近悉尼或布里斯班给几个地标（演示用）
    sydney = [
        {"name": "Sydney Opera House", "lat": -33.857, "lon": 151.215, "category": "attraction"},
        {"name": "Sydney Harbour Bridge", "lat": -33.852, "lon": 151.210, "category": "attraction"},
        {"name": "Royal Botanic Garden", "lat": -33.864, "lon": 151.216, "category": "park"},
        {"name": "The Rocks", "lat": -33.859, "lon": 151.207, "category": "attraction"},
    ]
    brisbane = [
        {"name": "South Bank Parklands", "lat": -27.474, "lon": 153.020, "category": "park"},
        {"name": "Museum of Brisbane", "lat": -27.469, "lon": 153.022, "category": "museum"},
        {"name": "Mount Coot-Tha Lookout", "lat": -27.471, "lon": 152.946, "category": "viewpoint"},
        {"name": "Roma Street Parkland", "lat": -27.462, "lon": 153.020, "category": "park"},
    ]

    import math
    def dist2(a,b): return (a[0]-b[0])**2 + (a[1]-b[1])**2
    if dist2((lat,lon),(-33.86,151.21)) < dist2((lat,lon),(-27.47,153.02)):
        pool = sydney
    else:
        pool = brisbane
    return pool[:max(1,limit)]
