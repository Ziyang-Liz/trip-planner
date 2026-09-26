"""Explicit, timezone-aware contract for a bounded replanning horizon."""

from typing import Annotated, Literal
from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, model_validator


class Model(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)


class Location(Model):
    lat: float = Field(ge=-90, le=90)
    lon: float = Field(ge=-180, le=180)


class Window(Model):
    start: AwareDatetime
    end: AwareDatetime

    @model_validator(mode="after")
    def ordered(self):
        if self.end <= self.start:
            raise ValueError("end must be after start")
        return self


class Place(Model):
    id: str = Field(min_length=1, max_length=100)
    name: str = Field(min_length=1, max_length=200)
    location: Location | None = None
    outdoor: bool | None = None
    outdoor_verified: bool = False
    duration_minutes: int | None = Field(default=None, ge=1, le=1440)
    duration_verified: bool = False
    cost: float | None = Field(default=None, ge=0, le=1_000_000_000, multiple_of=0.01)
    cost_verified: bool = False
    # None = unknown. [] = confirmed closed throughout the planning horizon.
    opening_windows: list[Window] | None = Field(default=None, max_length=30)


class Activity(Window):
    id: str = Field(min_length=1, max_length=100)
    place: Place
    must_visit: bool = False
    fixed_time: bool = False
    cancellation_cost: float | None = Field(default=None, ge=0, le=1_000_000_000, multiple_of=0.01)


class LateDeparture(Model):
    type: Literal["late_departure"]
    planned_departure: AwareDatetime
    delay_minutes: int = Field(ge=1, le=720)


class Rain(Window):
    type: Literal["rain"]


Event = Annotated[LateDeparture | Rain, Field(discriminator="type")]


class ReplanRequest(Model):
    activities: list[Activity] = Field(min_length=1, max_length=8)
    candidates: list[Place] = Field(default_factory=list, max_length=20)
    current_time: AwareDatetime
    current_location: Location
    horizon_end: AwareDatetime
    completed_activity_ids: list[str] = Field(default_factory=list)
    locked_activity_ids: list[str] = Field(default_factory=list)
    event: Event
    total_budget: float = Field(ge=0, le=1_000_000_000, multiple_of=0.01)
    # Already committed expenses OUTSIDE activities, including other days.
    committed_cost: float = Field(default=0, ge=0, le=1_000_000_000, multiple_of=0.01)
    committed_cost_verified: bool = False
    # A confirmed FIXED fare covering all alternatives (e.g. day pass), not a
    # distance-dependent taxi quote. None means no complete fare information.
    transport_cost: float | None = Field(default=None, ge=0, le=1_000_000_000, multiple_of=0.01)
    original_schedule_verified: bool = False

    @model_validator(mode="after")
    def consistent(self):
        ids = [a.id for a in self.activities]
        if len(ids) != len(set(ids)):
            raise ValueError("activity IDs must be unique")
        for selected in (self.completed_activity_ids, self.locked_activity_ids):
            if len(selected) != len(set(selected)) or not set(selected) <= set(ids):
                raise ValueError("completed/locked IDs must be unique existing activity IDs")
        if self.horizon_end <= self.current_time:
            raise ValueError("horizon_end must be after current_time")
        if (self.horizon_end - self.current_time).total_seconds() > 7 * 86400:
            raise ValueError("planning horizon is limited to seven days")
        if any(a.end > self.current_time for a in self.activities if a.id in self.completed_activity_ids):
            raise ValueError("completed activities cannot end after current_time")
        known = {}
        for p in [a.place for a in self.activities] + self.candidates:
            if p.id in known and known[p.id] != p:
                raise ValueError("the same place ID must have consistent metadata")
            known[p.id] = p
        if len({p.id for p in self.candidates}) != len(self.candidates):
            raise ValueError("candidate IDs must be unique")
        return self


class Issue(Model):
    code: str
    message: str
    activity_ids: list[str] = Field(default_factory=list)


class ScheduledActivity(Activity):
    travel_minutes: float = 0
    travel_distance_km: float | None = None
    travel_source: str = "none"


class Change(Model):
    activity_id: str
    action: Literal["completed", "retained", "moved", "replaced", "deleted"]
    before: Activity
    after: Activity | None
    reasons: list[str]


class Alternative(Model):
    objective: Literal["minimum_change", "minimum_extra_cost", "minimum_travel"]
    label: str
    feasibility: Literal["verified", "conditional"]
    activities: list[Activity | ScheduledActivity]
    changes: list[Change]
    end_time: AwareDatetime
    elapsed_minutes: float
    travel_minutes: float
    travel_distance_km: float | None
    known_cost: float
    estimated_total_cost: float | None
    extra_cost: float | None
    unverified: list[Issue]


class Timings(Model):
    data_fetch_ms: float
    replanning_compute_ms: float
    end_to_end_ms: float


class ReplanResponse(Model):
    status: Literal["ok", "limited_alternatives", "no_feasible_solution", "search_limit", "insufficient_data"]
    original_conflicts: list[Issue]
    unverified_constraints: list[Issue]
    alternatives: list[Alternative]
    blocking_constraints: list[Issue]
    notices: list[str]
    search_truncated: bool
    evaluated_states: int
    data_sources: dict[str, str]
    timings: Timings
