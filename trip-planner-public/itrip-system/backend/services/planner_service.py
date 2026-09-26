# backend/services/planner_service.py

def build_weather_advice(weather):
    if weather.get("source") in ("demo", "unavailable"):
        return "Weather is unverified. Check a current forecast before choosing outdoor activities."
    rain = weather.get("rain_probability") or 0
    temp_max = weather.get("temp_max") or weather.get("temp") or 25

    if rain >= 60:
        return "Rain is likely, so indoor attractions such as museums, shopping centres, and galleries are recommended."

    if rain >= 40:
        return "Some rain is possible, so it is better to keep a flexible plan with both indoor and outdoor options."

    if temp_max >= 32:
        return "The weather may be hot, so outdoor activities are better in the morning and indoor activities are recommended in the afternoon."

    return "The weather is suitable for outdoor sightseeing and general travel activities."


def score_place(place, weather, preference, daily_budget):
    score = 0

    tags = place.get("tags", [])
    rain = weather.get("rain_probability") or 0
    temp_max = weather.get("temp_max") or weather.get("temp") or 25
    cost = place.get("estimated_cost", 0)

    # Weather-based scoring
    if weather.get("source") == "unavailable":
        pass
    elif rain >= 60:
        if "indoor" in tags:
            score += 30
        if "outdoor" in tags:
            score -= 20
        if "nature" in tags:
            score -= 10
    else:
        if "outdoor" in tags:
            score += 20
        if "nature" in tags:
            score += 15

    if temp_max >= 32:
        if "indoor" in tags:
            score += 20
        if "outdoor" in tags:
            score -= 10

    # Preference-based scoring
    pref = preference.lower()

    if pref == "popular":
        score += 5
    elif pref in tags:
        score += 25

    # Budget-based scoring
    if cost <= daily_budget:
        score += 10
    else:
        score -= 30

    return score


def build_daily_itinerary(weather_days, places, days, preference="Popular", budget=800):
    if not places:
        return []

    daily_budget = budget / days if days > 0 else budget
    used_places = set()
    itinerary = []

    activities_per_day = 3

    for i in range(days):
        weather = weather_days[i] if i < len(weather_days) else {
            "source": "unavailable",
            "date": f"Day {i + 1}",
            "temp": None,
            "temp_max": None,
            "weather": "unknown",
            "rain_probability": None
        }

        # Step 1: first try to use places that have not been recommended before
        unused_places = [
            place for place in places
            if place.get("name") not in used_places
        ]

        ranked_unused_places = sorted(
            unused_places,
            key=lambda place: score_place(place, weather, preference, daily_budget),
            reverse=True
        )

        selected_places = ranked_unused_places[:activities_per_day]

        # Step 2: if there are not enough unused places, allow repeated places
        if len(selected_places) < activities_per_day:
            selected_names = {place.get("name") for place in selected_places}

            reusable_places = [
                place for place in places
                if place.get("name") not in selected_names
            ]

            ranked_reusable_places = sorted(
                reusable_places,
                key=lambda place: score_place(place, weather, preference, daily_budget),
                reverse=True
            )

            needed = activities_per_day - len(selected_places)
            selected_places.extend(ranked_reusable_places[:needed])

        # Step 3: record selected places as used
        for place in selected_places:
            used_places.add(place.get("name"))

        itinerary.append({
            "day": i + 1,
            "date": weather.get("date", f"Day {i + 1}"),
            "weather": weather,
            "advice": build_weather_advice(weather),
            "activities": selected_places
        })

    return itinerary
