import time

from fastapi import APIRouter, HTTPException, Query
from services.upstream_errors import PlacesError
from services.places_service import get_places
from services.weather_service import get_weather
from services.planner_service import build_daily_itinerary


router = APIRouter(prefix="/plan", tags=["Trip"])


@router.get("/")
def generate_trip(
    origin: str = Query(..., min_length=1),
    destination: str = Query(..., min_length=1),
    days: int = Query(3, ge=1, le=14),
    budget: float = Query(800, ge=0),
    preference: str = Query("Popular")
):
    start_time = time.time()
    origin = origin.strip()
    destination = destination.strip()
    if not origin or not destination:
        raise HTTPException(422, "Origin and destination must contain a city name.")

    try:
        places = get_places(destination)
    except PlacesError as error:
        raise HTTPException(error.status_code, str(error)) from None
    weather = get_weather(destination, days)

    daily_plan = build_daily_itinerary(
        weather_days=weather,
        places=places,
        days=days,
        preference=preference,
        budget=budget
    )

    response_time_ms = round((time.time() - start_time) * 1000, 2)

    return {
        "origin": origin,
        "destination": destination,
        "days": days,
        "budget": budget,
        "preference": preference,
        "places": places,
        "weather": weather,
        "daily_plan": daily_plan,
        "response_time_ms": response_time_ms
    }
