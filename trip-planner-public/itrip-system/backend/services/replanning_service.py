"""Bounded multi-objective beam search. No known hard constraint is relaxed."""

from dataclasses import dataclass
from datetime import timedelta
from core.replanning_models import Activity, ScheduledActivity, Rain, LateDeparture, Issue

OBJECTIVES = (
    ("minimum_change", "最少改动"),
    ("minimum_extra_cost", "最低额外费用"),
    ("minimum_travel", "最少路程耗时"),
)
BEAM_WIDTH = 60
MAX_EVALUATIONS = 100_000


def issue(code, message, *ids):
    return Issue(code=code, message=message, activity_ids=list(ids)).model_dump()


def ready_time(req):
    if isinstance(req.event, LateDeparture):
        return max(req.current_time, req.event.planned_departure + timedelta(minutes=req.event.delay_minutes))
    return req.current_time


def overlap(start, end, window):
    return start < window.end and end > window.start


def duration(activity, place):
    if place.duration_minutes is not None:
        return place.duration_minutes
    if place.id == activity.place.id:
        return (activity.end - activity.start).total_seconds() / 60
    return None


def plain(activity):
    return {k: v for k, v in activity.model_dump(mode="json").items() if k in Activity.model_fields}


def cost_info(req, chosen, remaining=()):
    # Count completed activities exactly once; committed_cost excludes them.
    amounts = [req.committed_cost, req.transport_cost]
    amounts += [a.place.cost for a in req.activities if a.id in req.completed_activity_ids]
    amounts += [a.place.cost for a in chosen]
    by_id = {a.id: a for a in chosen}
    for old in req.activities:
        if old.id in req.completed_activity_ids or old.id in remaining:
            continue
        after = by_id.get(old.id)
        if after is None or after.place.id != old.place.id:
            amounts.append(old.cancellation_cost)
    known = round(sum(v for v in amounts if v is not None), 2)
    return known, sum(v is None for v in amounts)


def get_leg(legs, start, end):
    return legs.get((start, "place:" + end))


def validate_original(req, legs):
    conflicts = []
    cursor, location = ready_time(req), "@current"
    remaining = sorted((a for a in req.activities if a.id not in req.completed_activity_ids), key=lambda a: a.start)
    for a in remaining:
        leg = get_leg(legs, location, a.place.id)
        if not leg or leg["minutes"] is None:
            conflicts.append(issue("travel_unavailable", "无法验证到达该活动的交通时间。", a.id))
        elif cursor + timedelta(minutes=leg["minutes"]) > a.start:
            arrival = cursor + timedelta(minutes=leg["minutes"])
            conflicts.append(issue("late_arrival", f"预计最早 {arrival.isoformat()} 到达，晚于原开始时间 {a.start.isoformat()}。", a.id))
        if a.end > req.horizon_end:
            conflicts.append(issue("horizon", "原活动结束时间超过规划截止时间。", a.id))
        if duration(a, a.place) > (a.end-a.start).total_seconds()/60:
            conflicts.append(issue("duration", "原时段不足以完成所需停留时间。", a.id))
        if a.place.opening_windows is not None and not any(w.start <= a.start and a.end <= w.end for w in a.place.opening_windows):
            conflicts.append(issue("opening_hours", "原活动不完全处于已提供的开放时段内。", a.id))
        if isinstance(req.event, Rain) and a.place.outdoor is True and overlap(a.start, a.end, req.event):
            conflicts.append(issue("rain", "原户外活动时段与降雨重叠。", a.id))
        cursor, location = max(cursor, a.end), "place:" + a.place.id
    known, _ = cost_info(req, remaining)
    if known > req.total_budget:
        conflicts.append(issue("budget", f"原行程已知费用 {known:.2f} 超过总预算 {req.total_budget:.2f}。"))
    return conflicts


@dataclass
class State:
    remaining: tuple
    chosen: tuple
    cursor: object
    location: str
    used: frozenset
    travel: float = 0


def state_rank(req, state, objective):
    chosen = {a.id: a for a in state.chosen}
    deleted = replaced = moved = shift = 0
    for old in req.activities:
        if old.id in req.completed_activity_ids or old.id in state.remaining:
            continue
        new = chosen.get(old.id)
        if new is None:
            deleted += 1
        elif new.place.id != old.place.id:
            replaced += 1
        elif new.start != old.start or new.end != old.end:
            moved += 1
            shift += abs((new.start-old.start).total_seconds())/60
    cost, missing = cost_info(req, state.chosen, state.remaining)
    disruption = (deleted + replaced, deleted, moved, shift)
    if objective == 0:
        return (*disruption, missing, cost, state.travel)
    if objective == 1:
        return (missing, cost, *disruption, state.travel)
    return (state.travel, *disruption, missing, cost)


def schedule_options(req, old, place, state, legs):
    leg = get_leg(legs, state.location, place.id)
    if not leg:
        return [], issue("travel_unavailable", "缺少坐标或交通数据，无法验证交通衔接。", old.id)
    if leg["minutes"] is None:
        return [], issue("unreachable", "路线提供方未找到该路段的驾车路线。", old.id)
    minutes = duration(old, place)
    if minutes is None:
        return [], issue("duration_unknown", "替换景点缺少停留时间，无法排入时间表。", old.id)
    fixed = old.fixed_time or old.id in req.locked_activity_ids
    arrival = state.cursor + timedelta(minutes=leg["minutes"])
    if fixed:
        if arrival > old.start or minutes > (old.end-old.start).total_seconds()/60:
            return [], issue("fixed_appointment", f"最早到达 {arrival.isoformat()}；预约 {old.start.isoformat()} 至 {old.end.isoformat()}，所需停留 {minutes:g} 分钟，无法满足。", old.id)
        starts = [old.start]
        minutes = (old.end-old.start).total_seconds()/60
    else:
        starts = [arrival, max(arrival, old.start)]
    options = []
    for initial in starts:
        windows = place.opening_windows
        possible_windows = windows if windows is not None else [None]
        for window in possible_windows:
            start = initial if window is None else max(initial, window.start)
            end = start + timedelta(minutes=minutes)
            if isinstance(req.event, Rain) and place.outdoor is True and overlap(start, end, req.event):
                start = req.event.end
                end = start + timedelta(minutes=minutes)
            if fixed and (start != old.start or end != old.end):
                continue
            if end > req.horizon_end or (window is not None and end > window.end):
                continue
            item = ScheduledActivity(
                **{**old.model_dump(), "place": place, "start": start, "end": end},
                travel_minutes=leg["minutes"], travel_distance_km=leg["distance_km"], travel_source=leg["source"],
            )
            if not any(x.start == start and x.end == end for x in options):
                options.append(item)
            # Later opening windows can be useful before/after fixed appointments.
    if not options:
        return [], issue("time_window", f"{place.name} 从最早到达 {arrival.isoformat()} 起需要 {minutes:g} 分钟；在开放窗口、降雨限制、预约及截止 {req.horizon_end.isoformat()} 内无法排入。", old.id)
    return options, None


def unverified_constraints(req, chosen, legs):
    warnings = []
    if not req.original_schedule_verified:
        warnings.append(issue("original_schedule", "原始起止时间尚未由用户核对；改动量仅相对此时间表计算。"))
    if not req.committed_cost_verified:
        warnings.append(issue("other_costs", "其他日期、住宿、餐饮和已支付费用是否完整，未验证。"))
    if req.transport_cost is None:
        warnings.append(issue("transport_cost", "交通费用未验证，已知费用不等于完整总费用。"))
    cursor = "@current"
    for a in chosen:
        p = a.place
        if p.opening_windows is None:
            warnings.append(issue("opening_hours", "景点开放时段未验证。", a.id))
        if (p.outdoor is None or not p.outdoor_verified) and isinstance(req.event, Rain):
            warnings.append(issue("indoor_outdoor", "活动是否适合降雨天气未验证。", a.id))
        if not p.duration_verified or p.duration_minutes is None:
            warnings.append(issue("duration", "停留时间使用估计值，未验证。", a.id))
        if not p.cost_verified or p.cost is None:
            warnings.append(issue("activity_cost", "景点费用使用估计值或缺失，未验证。", a.id))
        leg = get_leg(legs, cursor, p.id)
        if not leg or not leg.get("verified", False):
            warnings.append(issue("travel_time", f"交通时间未验证（{a.travel_source}）；OSRM 不包含实时交通，直线估计不代表道路路线。", a.id))
        cursor = "place:" + p.id
    kept = {a.id: a for a in chosen}
    for a in req.activities:
        if a.id in req.completed_activity_ids:
            if a.place.cost is None or not a.place.cost_verified:
                warnings.append(issue("completed_cost", "已完成活动费用未验证，仍计入总预算。", a.id))
        elif a.id not in kept or kept[a.id].place.id != a.place.id:
            if a.cancellation_cost is None:
                warnings.append(issue("cancellation_cost", "删除或替换该活动的取消费用未验证。", a.id))
    return warnings


def alternative(req, state, objective, label, legs, conflicts):
    by_id = {a.id: a for a in state.chosen}
    completed = [a for a in req.activities if a.id in req.completed_activity_ids]
    changes = []
    for old in req.activities:
        new = by_id.get(old.id)
        if old.id in req.completed_activity_ids:
            action, new, reasons = "completed", old, ["已完成活动保持原样。"]
        else:
            reasons = [c["message"] for c in conflicts if old.id in c["activity_ids"]]
            if new is None:
                action = "deleted"
                reasons.append("移除非必去、非锁定活动，以满足约束或降低该方案的费用／交通耗时。")
            elif new.place.id != old.place.id:
                action = "replaced"
                reasons.append("从原候选池替换为符合已知时间、天气和预算约束的活动。")
            elif new.start != old.start or new.end != old.end:
                action = "moved"
                reasons.append("调整起止时间或顺序，以容纳出发延迟、交通、开放时段或降雨。")
            else:
                action = "retained"
                reasons.append("保留原地点和原时间。")
        changes.append({"activity_id": old.id, "action": action, "before": plain(old), "after": plain(new) if new else None, "reasons": reasons})
    known, missing = cost_info(req, state.chosen)
    original_amounts = [a.place.cost for a in req.activities] + [req.committed_cost, req.transport_cost]
    original_cost = sum(original_amounts) if all(x is not None for x in original_amounts) else None
    warnings = unverified_constraints(req, state.chosen, legs)
    distances = [a.travel_distance_km for a in state.chosen]
    return {
        "objective": objective, "label": label,
        "feasibility": "conditional" if warnings else "verified",
        "activities": [a.model_dump(mode="json") for a in completed] + [a.model_dump(mode="json") for a in state.chosen],
        "changes": changes, "end_time": state.cursor,
        "elapsed_minutes": round(max(0, (state.cursor-ready_time(req)).total_seconds()/60), 2),
        "travel_minutes": round(state.travel, 2),
        "travel_distance_km": round(sum(distances), 2) if all(d is not None for d in distances) else None,
        "known_cost": known, "estimated_total_cost": known if not missing else None,
        "extra_cost": round(known-original_cost, 2) if not missing and original_cost is not None else None,
        "unverified": warnings,
    }


def replan(req, legs):
    conflicts = validate_original(req, legs)
    remaining = {a.id: a for a in req.activities if a.id not in req.completed_activity_ids}
    baseline, location = [], "@current"
    for a in sorted(remaining.values(), key=lambda a: a.start):
        leg = get_leg(legs, location, a.place.id)
        baseline.append(ScheduledActivity(**a.model_dump(), travel_source=leg["source"] if leg else "missing"))
        location = "place:" + a.place.id
    input_warnings = unverified_constraints(req, baseline, legs)
    original_places = {a.place.id for a in req.activities}
    replacements = [p for p in req.candidates if p.id not in original_places]
    beam = [State(tuple(remaining), (), ready_time(req), "@current", frozenset())]
    failures, finals = {}, []
    evaluated, truncated = 0, False
    if not remaining:
        finals = beam
    for _ in range(len(remaining)):
        expanded = []
        for state in beam:
            for aid in state.remaining:
                old = remaining[aid]
                rest = tuple(x for x in state.remaining if x != aid)
                protected = old.must_visit or old.fixed_time or aid in req.locked_activity_ids
                if not protected:
                    expanded.append(State(rest, state.chosen, state.cursor, state.location, state.used, state.travel))
                for place in [old.place] + ([] if protected else replacements):
                    if place.id in state.used and place.id != old.place.id:
                        continue
                    evaluated += 1
                    if evaluated > MAX_EVALUATIONS:
                        truncated = True
                        break
                    options, error = schedule_options(req, old, place, state, legs)
                    if error:
                        failures[(error["code"], aid)] = error
                    for a in options:
                        next_state = State(rest, state.chosen+(a,), a.end, "place:"+place.id, state.used | {place.id}, state.travel+a.travel_minutes)
                        known, _missing = cost_info(req, next_state.chosen, rest)
                        if known > req.total_budget:
                            failures[("budget", aid)] = issue("budget", f"候选方案已知费用 {known:.2f} 超过总预算 {req.total_budget:.2f}。", aid)
                        else:
                            expanded.append(next_state)
                if evaluated > MAX_EVALUATIONS:
                    break
            if evaluated > MAX_EVALUATIONS:
                break
        unique = {}
        for s in expanded:
            signature = (s.remaining, tuple((a.id, a.place.id, a.start, a.end) for a in s.chosen))
            unique[signature] = s
        states = list(unique.values())
        # Keep diverse partial solutions for all three objectives.
        if len(states) > BEAM_WIDTH:
            truncated = True
            selected = {}
            for objective in range(3):
                for s in sorted(states, key=lambda s: state_rank(req, s, objective))[:BEAM_WIDTH//3]:
                    selected[id(s)] = s
            states = list(selected.values())
        beam = states
        if not beam or evaluated > MAX_EVALUATIONS:
            break
    if remaining:
        finals = [s for s in beam if not s.remaining and s.chosen]
    # Deletion branches must also pass budget checks, including sunk/other costs.
    finals = [s for s in finals if cost_info(req, s.chosen)[0] <= req.total_budget]
    if not finals and not failures:
        if truncated:
            failures[("search_limit", "")] = issue("search_limit", "在候选评估上限内未找到完整方案，无法判定绝对无解。")
        else:
            failures[("budget", "")] = issue("budget_or_empty", "预算不足，或无法保留至少一项未完成活动。")
    alternatives, selected_signatures, selected_structures = [], set(), set()
    for idx, (objective, label) in enumerate(OBJECTIVES):
        ranked = sorted(finals, key=lambda s: state_rank(req, s, idx))
        # Prefer a different activity combination/order over a cosmetic time shift.
        different = [s for s in ranked if tuple((a.id, a.place.id) for a in s.chosen) not in selected_structures]
        for s in different + ranked:
            signature = tuple((a.id, a.place.id, a.start, a.end) for a in s.chosen)
            if signature not in selected_signatures:
                selected_signatures.add(signature)
                selected_structures.add(tuple((a.id, a.place.id) for a in s.chosen))
                alternatives.append(alternative(req, s, objective, label, legs, conflicts))
                break
    notices = ["三个目标分别排序并去重，优先展示不同活动组合或顺序，再考虑不同时间；不保证全局最优。费用目标优先费用数据完整的候选，其次比较已知费用。", "预算包括已完成活动、保留／替换活动、已知取消费、固定交通费及其他已承诺费用；缺失费用不视为零。交通按驾车模式估算。"]
    if truncated:
        notices.append("候选搜索有界，已剪枝；未找到方案时不能据此证明问题绝对无解。")
    if 0 < len(alternatives) < 3:
        notices.append(f"仅找到 {len(alternatives)} 种不同方案，无法诚实提供三种不同方案。")
    if alternatives:
        status = "ok" if len(alternatives) == 3 else "limited_alternatives"
    elif truncated:
        status = "search_limit"
    elif any(k[0] in ("travel_unavailable", "duration_unknown") for k in failures):
        status = "insufficient_data"
    else:
        status = "no_feasible_solution"
    return {
        "status": status, "original_conflicts": conflicts, "unverified_constraints": input_warnings, "alternatives": alternatives,
        "blocking_constraints": list(failures.values()) if not alternatives else [],
        "notices": notices, "search_truncated": truncated, "evaluated_states": min(evaluated, MAX_EVALUATIONS),
    }
