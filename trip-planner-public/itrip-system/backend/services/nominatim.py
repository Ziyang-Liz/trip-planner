import os, urllib.parse
from .utils import http_client, http_timeout

USER_AGENT = os.getenv("USER_AGENT", "TripPlanner-Demo/1.0 (contact@example.com)")

async def geocode(place: str) -> tuple[float, float]:
    q = urllib.parse.quote(place)
    url = f"https://nominatim.openstreetmap.org/search?q={q}&format=json&limit=1"
    headers = {"User-Agent": USER_AGENT}
    async with http_client() as client:
        r = await client.get(url, headers=headers, timeout=http_timeout(8))
        r.raise_for_status()
        js = r.json()
        if not js:
            raise ValueError(f"Geocoding failed for {place}")
        return float(js[0]["lat"]), float(js[0]["lon"])
