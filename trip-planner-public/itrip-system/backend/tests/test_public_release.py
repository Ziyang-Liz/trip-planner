import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

import requests
from fastapi.testclient import TestClient

from main import app
from services.planner_service import build_daily_itinerary
from services.weather_service import get_weather


class PublicReleaseTests(unittest.TestCase):
    def test_missing_attractions_key_has_actionable_response(self):
        with patch("services.places_service.get_valid_cache", return_value=None), patch(
            "services.places_service.settings", SimpleNamespace(opentripmap_api_key="")
        ):
            response = TestClient(app).get("/plan/", params={"origin": "Brisbane", "destination": "Brisbane"})
        self.assertEqual(response.status_code, 503)
        self.assertIn("OPENTRIPMAP_API_KEY", response.json()["detail"])

    def test_upstream_failures_do_not_leak_keys_in_logs_or_http(self):
        secret = "test-secret-not-a-real-key"
        for error, expected in [
            (requests.Timeout(f"url?apikey={secret}"), 504),
            (requests.ConnectionError(f"url?apikey={secret}"), 502),
            (requests.HTTPError(f"url?apikey={secret}", response=SimpleNamespace(status_code=401)), 502),
            (ValueError(f"invalid JSON {secret}"), 502),
        ]:
            with self.subTest(error=type(error).__name__), patch(
                "services.places_service.get_valid_cache", return_value=None
            ), patch("services.places_service.settings", SimpleNamespace(opentripmap_api_key=secret)), patch(
                "services.places_service.requests.get", side_effect=error
            ), self.assertLogs("services.upstream_errors", level="WARNING") as logs:
                response = TestClient(app).get("/plan/", params={"origin": "Brisbane", "destination": "Brisbane"})
            self.assertEqual(response.status_code, expected)
            self.assertNotIn(secret, response.text + "".join(logs.output))

    def test_unknown_city_has_validation_response(self):
        with patch("services.places_service.get_valid_cache", return_value=None), patch(
            "services.places_service.settings", SimpleNamespace(opentripmap_api_key="test")
        ), patch("services.places_service.request_places", return_value={}):
            response = TestClient(app).get("/plan/", params={"origin": "Brisbane", "destination": "Unknown"})
        self.assertEqual(response.status_code, 422)

    def test_whitespace_city_rejected_before_upstream_request(self):
        with patch("routers.trip.get_places") as places:
            response = TestClient(app).get("/plan/", params={"origin": " ", "destination": "Brisbane"})
        self.assertEqual(response.status_code, 422)
        places.assert_not_called()

    def test_missing_weather_key_labels_every_requested_day_as_demo(self):
        with patch("services.weather_service.get_valid_cache", return_value=None), patch(
            "services.weather_service.settings", SimpleNamespace(openweather_api_key="")
        ), patch("services.weather_service.requests.get") as request:
            weather = get_weather("Brisbane", 14)
        self.assertEqual(len(weather), 14)
        self.assertTrue(all(day["source"] == "demo" for day in weather))
        self.assertEqual(len({day["date"] for day in weather}), 14)
        request.assert_not_called()

    def test_weather_error_is_redacted_and_fallback_identified(self):
        secret = "test-weather-secret"
        with patch("services.weather_service.get_valid_cache", return_value=None), patch(
            "services.weather_service.settings", SimpleNamespace(openweather_api_key=secret)
        ), patch("services.weather_service.requests.get", side_effect=requests.HTTPError(f"url?appid={secret}")), self.assertLogs(
            "services.upstream_errors", level="WARNING"
        ) as logs:
            weather = get_weather("Brisbane")
        self.assertNotIn(secret, "".join(logs.output))
        self.assertTrue(all(day["source"] == "demo" for day in weather))

    def test_forecast_and_cache_sources_and_missing_days(self):
        forecast = {"list": [{"dt_txt": "2026-10-01 12:00:00", "main": {
            "temp": 25, "temp_min": 20, "temp_max": 28
        }, "weather": [{"description": "clear sky"}], "pop": 0.1}]}
        with patch("services.weather_service.get_valid_cache", return_value=None), patch(
            "services.weather_service.settings", SimpleNamespace(openweather_api_key="test")
        ), patch("services.weather_service.requests.get", return_value=Mock(json=Mock(return_value=forecast))), patch(
            "services.weather_service.save_cache"
        ):
            weather = get_weather("Brisbane", 3)
        self.assertEqual(weather[0]["source"], "openweather")
        with patch("services.weather_service.get_valid_cache", return_value=weather), patch(
            "services.weather_service.requests.get"
        ) as request:
            cached = get_weather("Brisbane", 3)
        self.assertEqual(cached[0]["source"], "openweather_cache")
        self.assertEqual(weather[0]["source"], "openweather")
        request.assert_not_called()
        plan = build_daily_itinerary(weather, [{"name": "Park", "tags": ["outdoor"]}], 3)
        self.assertEqual(plan[1]["weather"]["source"], "unavailable")
        self.assertIsNone(plan[1]["weather"]["temp"])
        self.assertIn("unverified", plan[1]["advice"])


if __name__ == "__main__":
    unittest.main()
