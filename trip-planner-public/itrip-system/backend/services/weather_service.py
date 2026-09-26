# backend/services/weather_service.py

import requests
from core.config import settings
from services.api_cache_service import get_valid_cache, save_cache
from services.upstream_errors import log_upstream_error


def get_weather(city: str, days: int = 3):
    """
    Get weather forecast from OpenWeatherMap.
    Return one simplified forecast item per day.
    """
    cache_params = {
        "city": city.lower(),
        "days": days,
        "source_schema": 1
    }

    cached_weather = get_valid_cache("weather", cache_params)

    if cached_weather is not None:
        print("Weather loaded from database cache")
        return [{**item, "source": "openweather_cache"} for item in cached_weather]

    print("Weather loaded from OpenWeather API")
    api_key = settings.openweather_api_key
    if not api_key:
        return get_mock_weather(days)

    url = "https://api.openweathermap.org/data/2.5/forecast"

    params = {
        "q": city,
        "appid": api_key,
        "units": "metric"
    }

    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()

        data = response.json()
        forecast_list = data.get("list", [])

        daily_weather = []
        used_dates = set()

        for item in forecast_list:
            date_text = item.get("dt_txt", "")
            date = date_text.split(" ")[0]

            if date in used_dates:
                continue

            used_dates.add(date)

            weather_info = {
                "date": date,
                "source": "openweather",
                "temp": item["main"]["temp"],
                "temp_min": item["main"]["temp_min"],
                "temp_max": item["main"]["temp_max"],
                "weather": item["weather"][0]["description"],
                "rain_probability": int(item.get("pop", 0) * 100)
            }

            daily_weather.append(weather_info)

            if len(daily_weather) >= days:
                break
        if not daily_weather:
            return get_mock_weather(days)
        save_cache(
            cache_type="weather",
            params=cache_params,
            response_data=daily_weather,
            ttl_minutes=180
        )
        return daily_weather

    except Exception as e:
        log_upstream_error("OpenWeather", e)
        return get_mock_weather(days)


def get_mock_weather(days: int = 3):
    """
    Fallback weather data when API fails.
    This prevents the backend from crashing.
    """

    mock = [
        {
            "date": "Day 1",
            "temp": 25,
            "temp_min": 20,
            "temp_max": 28,
            "weather": "clear sky",
            "rain_probability": 10
        },
        {
            "date": "Day 2",
            "temp": 22,
            "temp_min": 18,
            "temp_max": 25,
            "weather": "light rain",
            "rain_probability": 65
        },
        {
            "date": "Day 3",
            "temp": 30,
            "temp_min": 24,
            "temp_max": 33,
            "weather": "hot weather",
            "rain_probability": 20
        }
    ]

    return [{**mock[i % len(mock)], "date": f"Day {i + 1}", "source": "demo"} for i in range(days)]
