# backend/services/places_service.py

import requests
from data.seed_places import get_seed_places
from core.config import settings
from services.api_cache_service import get_valid_cache, save_cache
from services.upstream_errors import PlacesError, log_upstream_error


def request_places(url, params):
    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.Timeout as error:
        log_upstream_error("OpenTripMap", error)
        raise PlacesError(504, "The attractions service timed out. Please try again.") from None
    except (requests.RequestException, ValueError) as error:
        log_upstream_error("OpenTripMap", error)
        raise PlacesError(502, "The attractions service is unavailable. Please try again or ask the operator to check its configuration.") from None


def get_city_coordinates(city: str):
    

    api_key = settings.opentripmap_api_key

    if not api_key:
        raise PlacesError(503, "Attractions are not configured. Set OPENTRIPMAP_API_KEY in backend/.env and restart the backend.")

    url = "https://api.opentripmap.com/0.1/en/places/geoname"

    params = {
        "name": city,
        "apikey": api_key
    }

    data = request_places(url, params)
    if not isinstance(data, dict):
        raise PlacesError(502, "The attractions service returned an invalid city response.")

    lat = data.get("lat")
    lon = data.get("lon")

    if lat is None or lon is None:
        raise PlacesError(422, "City not found. Please check the destination name.")

    return {
        "lat": lat,
        "lon": lon
    }


def convert_kinds_to_tags(kinds: str):
    
    kinds_lower = kinds.lower() if kinds else ""
    tags = []

    # indoor / culture
    if (
        "museums" in kinds_lower
        or "cultural" in kinds_lower
        or "theatres" in kinds_lower
        or "galleries" in kinds_lower
    ):
        tags.extend(["indoor", "culture"])

    # outdoor / nature
    if (
        "natural" in kinds_lower
        or "parks" in kinds_lower
        or "gardens" in kinds_lower
        or "beaches" in kinds_lower
        or "view_points" in kinds_lower
    ):
        tags.extend(["outdoor", "nature"])

    # food
    if (
        "foods" in kinds_lower
        or "restaurants" in kinds_lower
        or "cafes" in kinds_lower
    ):
        tags.extend(["food", "indoor"])

    # adventure
    if (
        "sport" in kinds_lower
        or "amusements" in kinds_lower
        or "water_parks" in kinds_lower
        or "zoos" in kinds_lower
    ):
        tags.extend(["adventure", "outdoor"])

    # landmark / culture
    if (
        "architecture" in kinds_lower
        or "historic" in kinds_lower
        or "monuments" in kinds_lower
        or "interesting_places" in kinds_lower
    ):
        tags.extend(["culture", "landmark"])

    if not tags:
        tags.append("general")

    return list(set(tags))


def estimate_place_cost(tags):
   
    if "food" in tags:
        return 30

    if "adventure" in tags:
        return 45

    if "culture" in tags and "indoor" in tags:
        return 25

    if "nature" in tags:
        return 0

    return 10


def get_places(destination: str, limit: int = 20):
    
    cache_params = {
        "destination": destination.lower(),
        "limit": limit
    }

    cached_places = get_valid_cache("places", cache_params)

    if cached_places is not None:
        print("Places loaded from database cache")
        return cached_places

    print("Places loaded from OpenTripMap API")

    api_key = settings.opentripmap_api_key

    if not api_key:
        raise PlacesError(503, "Attractions are not configured. Set OPENTRIPMAP_API_KEY in backend/.env and restart the backend.")

    coords = get_city_coordinates(destination)

    url = "https://api.opentripmap.com/0.1/en/places/radius"

    params = {
        "radius": 20000,
        "lon": coords["lon"],
        "lat": coords["lat"],
        "rate": 1,
        "format": "json",
        "limit": limit,
        "kinds": "museums,cultural,natural,amusements,tourist_facilities,interesting_places",
        "apikey": api_key
    }

    raw_places = request_places(url, params)
    if not isinstance(raw_places, list) or any(not isinstance(item, dict) for item in raw_places):
        raise PlacesError(502, "The attractions service returned an invalid places response.")

    places = []

    for item in raw_places:
        name = item.get("name")

        if not name:
            continue

        point = item.get("point", {})
        lat = point.get("lat")
        lon = point.get("lon")

        if lat is None or lon is None:
            continue

        kinds = item.get("kinds", "")
        tags = convert_kinds_to_tags(kinds)

        kinds_lower = kinds.lower()
        name_lower = name.lower()
        bad_keywords = [
             "bank",
            "office",
            "building",
            "hotel",
            "apartment",
            "insurance",
            "commercial",
            "residential",
            "supermarket",
            "woolworths",
            "mall",
            "central"
        ]
        if any(keyword in name_lower for keyword in bad_keywords):
            continue

        if (
            "banks" in kinds_lower
            or "other_buildings_and_structures" in kinds_lower
            or "accomodations" in kinds_lower
            or "other_hotels" in kinds_lower
        ):
            continue
        tags = convert_kinds_to_tags(kinds)

        places.append({
            "name": name,
            "lat": lat,
            "lon": lon,
            "tags": tags,
            "kinds": kinds,
            "estimated_cost": estimate_place_cost(tags),
            "duration": 2
        })
    seed_places = get_seed_places(destination)

    existing_names = {place["name"].lower() for place in places}

    for seed in seed_places:
        if seed["name"].lower() not in existing_names:
            places.append(seed)

    places = sorted(
        places,
        key=lambda p: p.get("tourism_score", 0),
        reverse=True
    )

    final_places = places[:limit]

    save_cache(
        cache_type="places",
        params=cache_params,
        response_data=final_places,
        ttl_minutes=10080
    )

    return final_places
