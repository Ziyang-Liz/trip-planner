import unittest

from services.planner_service import build_daily_itinerary, score_place


class PlannerServiceTests(unittest.TestCase):
    def test_zero_days_does_not_divide_by_zero(self):
        self.assertEqual(build_daily_itinerary([], [{"name": "Park"}], 0), [])

    def test_weather_and_preference_affect_ranking(self):
        weather = {"rain_probability": 80, "temp_max": 25}
        museum = {"tags": ["indoor", "culture"], "estimated_cost": 10}
        park = {"tags": ["outdoor", "nature"], "estimated_cost": 0}

        self.assertGreater(
            score_place(museum, weather, "culture", 20),
            score_place(park, weather, "culture", 20),
        )


if __name__ == "__main__":
    unittest.main()
