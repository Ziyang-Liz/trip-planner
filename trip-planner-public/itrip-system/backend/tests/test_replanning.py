import unittest
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, patch
from pydantic import ValidationError
from fastapi.testclient import TestClient
from core.replanning_models import ReplanRequest, ReplanResponse
from services.replanning_service import replan, overlap
from services.replanning_data import fetch_travel_data, valid_matrix
from main import app


BASE = datetime(2026, 10, 1, tzinfo=timezone(timedelta(hours=10)))


def at(hour, minute=0):
    return BASE.replace(hour=hour, minute=minute).isoformat()


def place(pid, cost=10, outdoor=False):
    return {"id": pid, "name": pid, "location": {"lat": -27.47, "lon": 153.02},
            "outdoor": outdoor, "outdoor_verified": True, "duration_minutes": 30, "duration_verified": True,
            "cost": cost, "cost_verified": True,
            "opening_windows": [{"start": at(8), "end": at(18)}]}


def payload():
    return {
        "activities": [{"id": f"a{i}", "place": place(f"p{i}", 20+i*5, i == 0),
                        "start": at(9+i), "end": at(9+i, 30), "cancellation_cost": 0} for i in range(3)],
        "candidates": [place("museum", 5), place("gallery", 0), place("cafe", 15)],
        "current_time": at(8, 50), "current_location": {"lat": -27.47, "lon": 153.02},
        "horizon_end": at(18), "event": {"type": "late_departure", "planned_departure": at(8, 50), "delay_minutes": 40},
        "total_budget": 200, "transport_cost": 0, "committed_cost_verified": True,
        "original_schedule_verified": True,
    }


def travel(req, verified=True):
    keys = ["@current"] + ["place:"+p.id for p in [a.place for a in req.activities]+req.candidates]
    return {(a, b): {"minutes": 10 if a != b else 0, "distance_km": 3 if a != b else 0,
                     "source": "test_fixture", "verified": verified} for a in keys for b in keys}


class ReplanningTests(unittest.TestCase):
    def run_plan(self, raw):
        req = ReplanRequest.model_validate(raw)
        before = req.model_dump()
        result = replan(req, travel(req))
        self.assertEqual(before, req.model_dump(), "input must not be mutated")
        return req, result

    def test_late_departure_three_distinct_alternatives(self):
        req, result = self.run_plan(payload())
        self.assertEqual(len(result['alternatives']), 3)
        signatures = set()
        for alt in result['alternatives']:
            signatures.add(str(alt['activities']))
            self.assertLessEqual(alt['known_cost'], req.total_budget)
            self.assertGreaterEqual(datetime.fromisoformat(alt['activities'][0]['start']), BASE.replace(hour=9, minute=40))
        self.assertEqual(len(signatures), 3)
        self.assertTrue(any(c['code'] == 'late_arrival' for c in result['original_conflicts']))

    def test_rain_never_overlaps_known_outdoor_activity(self):
        raw = payload()
        raw['event'] = {'type': 'rain', 'start': at(9), 'end': at(12)}
        req, result = self.run_plan(raw)
        self.assertEqual(len(result['alternatives']), 3)
        self.assertTrue(any(c['code'] == 'rain' for c in result['original_conflicts']))
        for alt in result['alternatives']:
            for a in alt['activities']:
                if a['place']['outdoor']:
                    self.assertFalse(overlap(datetime.fromisoformat(a['start']), datetime.fromisoformat(a['end']), req.event))

    def test_locked_appointment_and_must_visit_survive(self):
        raw = payload()
        raw['activities'][1]['must_visit'] = True
        raw['locked_activity_ids'] = ['a2']
        _, result = self.run_plan(raw)
        self.assertTrue(result['alternatives'])
        for alt in result['alternatives']:
            by_id = {a['id']: a for a in alt['activities']}
            self.assertEqual(by_id['a1']['place']['id'], 'p1')
            self.assertEqual(by_id['a2']['start'], raw['activities'][2]['start'])
            self.assertEqual(by_id['a2']['end'], raw['activities'][2]['end'])

    def test_insufficient_budget_cannot_remove_required_activity(self):
        raw = payload()
        raw['activities'] = raw['activities'][:1]
        raw['activities'][0]['must_visit'] = True
        raw['total_budget'] = 1
        _, result = self.run_plan(raw)
        self.assertFalse(result['alternatives'])
        self.assertEqual(result['status'], 'no_feasible_solution')
        self.assertTrue(any(c['code'] == 'budget' for c in result['blocking_constraints']))

    def test_rain_and_fixed_outdoor_appointment_are_infeasible(self):
        raw = payload()
        raw['activities'] = raw['activities'][:1]
        raw['activities'][0]['fixed_time'] = True
        raw['event'] = {'type': 'rain', 'start': at(9), 'end': at(12)}
        _, result = self.run_plan(raw)
        self.assertEqual(result['status'], 'no_feasible_solution')
        self.assertFalse(result['alternatives'])

    def test_late_locked_appointment_is_not_moved(self):
        raw = payload()
        raw['activities'] = raw['activities'][:1]
        raw['locked_activity_ids'] = ['a0']
        _, result = self.run_plan(raw)
        self.assertFalse(result['alternatives'])
        self.assertTrue(any(c['code'] == 'fixed_appointment' for c in result['blocking_constraints']))

    def test_completed_activity_preserved_and_charged_once(self):
        raw = payload()
        raw['current_time'] = at(9, 40)
        raw['completed_activity_ids'] = ['a0']
        _, result = self.run_plan(raw)
        for alt in result['alternatives']:
            completed = next(a for a in alt['changes'] if a['activity_id'] == 'a0')
            self.assertEqual(completed['action'], 'completed')
            self.assertEqual(completed['before'], completed['after'])
            expected = sum(a['place']['cost'] for a in alt['activities'])
            self.assertEqual(alt['known_cost'], expected)

    def test_unknown_constraints_never_report_verified(self):
        raw = payload()
        raw['transport_cost'] = None
        for p in [a['place'] for a in raw['activities']] + raw['candidates']:
            p['opening_windows'] = None
            p['cost'] = None
            p['duration_verified'] = False
        _, result = self.run_plan(raw)
        for alt in result['alternatives']:
            self.assertEqual(alt['feasibility'], 'conditional')
            self.assertIsNone(alt['estimated_total_cost'])
            self.assertIsNone(alt['extra_cost'])
            self.assertTrue(any(w['code'] == 'opening_hours' for w in alt['unverified']))

    def test_closed_required_place_no_solution(self):
        raw = payload()
        raw['activities'] = raw['activities'][:1]
        raw['activities'][0]['must_visit'] = True
        raw['activities'][0]['place']['opening_windows'] = []
        _, result = self.run_plan(raw)
        self.assertFalse(result['alternatives'])

    def test_missing_travel_data_not_zero_minutes(self):
        req = ReplanRequest.model_validate(payload())
        result = replan(req, {})
        self.assertFalse(result['alternatives'])
        self.assertEqual(result['status'], 'insufficient_data')

    def test_known_unreachable_leg_is_not_missing_data(self):
        raw = payload()
        raw['activities'] = raw['activities'][:1]
        raw['activities'][0]['must_visit'] = True
        req = ReplanRequest.model_validate(raw)
        legs = travel(req)
        legs[('@current', 'place:p0')]['minutes'] = None
        result = replan(req, legs)
        self.assertEqual(result['status'], 'no_feasible_solution')
        self.assertEqual(result['blocking_constraints'][0]['code'], 'unreachable')

    def test_all_completed_returns_exact_original_activities(self):
        raw = payload()
        raw['current_time'] = at(14)
        raw['completed_activity_ids'] = [a['id'] for a in raw['activities']]
        req, result = self.run_plan(raw)
        self.assertEqual(len(result['alternatives']), 1)
        self.assertEqual(result['alternatives'][0]['activities'], [a.model_dump(mode='json') for a in req.activities])

    def test_no_solution_still_discloses_unknown_input_constraints(self):
        raw = payload()
        raw['activities'] = raw['activities'][:1]
        raw['activities'][0]['fixed_time'] = True
        raw['activities'][0]['place']['opening_windows'] = None
        _, result = self.run_plan(raw)
        self.assertFalse(result['alternatives'])
        self.assertTrue(any(w['code'] == 'opening_hours' for w in result['unverified_constraints']))

    def test_cancellation_and_committed_costs_enforce_budget(self):
        raw = payload()
        raw['activities'] = raw['activities'][:1]
        raw['activities'][0]['cancellation_cost'] = 30
        raw['committed_cost'] = 50
        raw['total_budget'] = 60
        _, result = self.run_plan(raw)
        self.assertFalse(result['alternatives'])

    def test_fewer_than_three_not_duplicated(self):
        raw = payload()
        raw['activities'] = raw['activities'][2:]
        raw['activities'][0]['fixed_time'] = True
        raw['candidates'] = []
        _, result = self.run_plan(raw)
        self.assertEqual(len(result['alternatives']), 1)
        self.assertEqual(result['status'], 'limited_alternatives')

    def test_invalid_ids_and_naive_datetimes_rejected(self):
        raw = payload()
        raw['locked_activity_ids'] = ['missing']
        with self.assertRaises(ValidationError):
            ReplanRequest.model_validate(raw)
        raw = payload()
        raw['current_time'] = '2026-10-01T09:00:00'
        with self.assertRaises(ValidationError):
            ReplanRequest.model_validate(raw)

    def test_current_time_does_not_double_count_delay(self):
        raw = payload()
        raw['activities'] = raw['activities'][:1]
        raw['activities'][0]['must_visit'] = True
        raw['current_time'] = at(9, 30)
        raw['candidates'] = []
        _, result = self.run_plan(raw)
        self.assertEqual(result['alternatives'][0]['activities'][0]['start'], at(9, 40))

    def test_subcent_cost_not_rounded_down_past_budget(self):
        raw = payload()
        raw['activities'][0]['place']['cost'] = 0.004
        with self.assertRaises(ValidationError):
            ReplanRequest.model_validate(raw)

    def test_known_windows_duration_and_travel_hold_for_all_outputs(self):
        raw = payload()
        raw['activities'][1]['place']['opening_windows'] = [{'start': at(12), 'end': at(14)}]
        req, result = self.run_plan(raw)
        self.assertTrue(result['alternatives'])
        for alt in result['alternatives']:
            cursor = BASE.replace(hour=9, minute=30)
            for a in alt['activities']:
                start, end = datetime.fromisoformat(a['start']), datetime.fromisoformat(a['end'])
                self.assertGreaterEqual(start, cursor+timedelta(minutes=a['travel_minutes']))
                self.assertGreaterEqual((end-start).total_seconds()/60, a['place']['duration_minutes'])
                self.assertTrue(any(datetime.fromisoformat(w['start']) <= start and end <= datetime.fromisoformat(w['end']) for w in a['place']['opening_windows']))
                self.assertLessEqual(end, req.horizon_end)
                cursor = end

    def test_search_cutoff_not_misrepresented_as_proven_infeasible(self):
        req = ReplanRequest.model_validate(payload())
        with patch('services.replanning_service.MAX_EVALUATIONS', 1):
            result = replan(req, travel(req))
        self.assertTrue(result['search_truncated'])
        self.assertEqual(result['status'], 'search_limit')

    def test_completed_future_end_rejected(self):
        raw = payload()
        raw['completed_activity_ids'] = ['a0']
        with self.assertRaises(ValidationError):
            ReplanRequest.model_validate(raw)

    def test_same_place_metadata_cannot_be_overridden_by_candidate(self):
        raw = payload()
        raw['candidates'].append(place('p0', 0))
        with self.assertRaises(ValidationError):
            ReplanRequest.model_validate(raw)

    def test_api_contract_timings_and_validation(self):
        raw = payload()
        req = ReplanRequest.model_validate(raw)
        with patch('routers.replan.fetch_travel_data', new=AsyncMock(return_value=(travel(req), {'travel': 'test_fixture'}))):
            with TestClient(app) as client:
                response = client.post('/plan/replan', json=raw)
                self.assertEqual(response.status_code, 200, response.text)
                result = ReplanResponse.model_validate(response.json())
                self.assertGreaterEqual(result.timings.end_to_end_ms, result.timings.replanning_compute_ms)
                self.assertIn('x-end-to-end-ms', response.headers)
                self.assertEqual(client.post('/plan/replan', json={}).status_code, 422)


class DataTests(unittest.IsolatedAsyncioTestCase):
    async def test_successful_matrix_is_cached_and_units_converted(self):
        req = ReplanRequest.model_validate(payload())
        size = 1 + len(req.activities) + len(req.candidates)
        data = {'code': 'Ok', 'durations': [[120]*size for _ in range(size)], 'distances': [[1000]*size for _ in range(size)]}
        with patch('services.replanning_data.get_cache', return_value=None), patch('services.replanning_data.set_cache') as memory, patch('services.replanning_data.get_valid_cache', return_value=None), patch('services.replanning_data.travel_matrix', new=AsyncMock(return_value=data)), patch('services.replanning_data.save_cache', return_value=True) as save:
            legs, source = await fetch_travel_data(req)
            self.assertEqual(source['travel'], 'osrm')
            self.assertEqual(source['cache_write'], 'saved')
            self.assertEqual(legs[('@current', 'place:p0')]['minutes'], 2)
            self.assertEqual(legs[('@current', 'place:p0')]['distance_km'], 1)
            self.assertEqual(save.call_args.args[-1], 15)
            memory.assert_called_once()

    async def test_database_cache_avoids_external_request(self):
        req = ReplanRequest.model_validate(payload())
        size = 1 + len(req.activities) + len(req.candidates)
        data = {k: [[0 if i == j else 60 for j in range(size)] for i in range(size)] for k in ('durations', 'distances')}
        with patch('services.replanning_data.get_cache', return_value=None), patch('services.replanning_data.set_cache'), patch('services.replanning_data.get_valid_cache', return_value=data), patch('services.replanning_data.travel_matrix', new_callable=AsyncMock) as http:
            legs, source = await fetch_travel_data(req)
            http.assert_not_called()
            self.assertEqual(source['travel'], 'postgres_cache')
            self.assertFalse(legs[('@current', 'place:p0')]['verified'])

    async def test_external_failure_has_explicit_unverified_estimate(self):
        req = ReplanRequest.model_validate(payload())
        with patch('services.replanning_data.get_cache', return_value=None), patch('services.replanning_data.get_valid_cache', return_value=None), patch('services.replanning_data.travel_matrix', new=AsyncMock(side_effect=OSError('offline'))):
            legs, source = await fetch_travel_data(req)
            self.assertEqual(source['travel'], 'estimated_straight_line')
            self.assertTrue(all(not leg['verified'] for leg in legs.values()))

    def test_invalid_cache_matrix_rejected(self):
        self.assertFalse(valid_matrix({'durations': [[float('nan')]], 'distances': [[0]]}, 1))
        self.assertFalse(valid_matrix({}, 3))


if __name__ == '__main__':
    unittest.main()
