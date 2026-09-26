import requests, os
from dotenv import load_dotenv
load_dotenv()

def get_places_between(origin, destination):
    api_key = os.getenv("GOOGLE_MAPS_API_KEY")
    url = "https://maps.googleapis.com/maps/api/directions/json"
    params = {"origin": origin, "destination": destination, "key": api_key}
    res = requests.get(url, params=params).json()

    steps = res["routes"][0]["legs"][0]["steps"][:5]
    return [
        {"name": s["html_instructions"], "distance": s["distance"]["text"]}
        for s in steps
    ]
