import asyncio
import logging
from time import perf_counter
from fastapi import APIRouter, Request
from core.replanning_models import ReplanRequest, ReplanResponse
from services.replanning_data import fetch_travel_data
from services.replanning_service import replan

router = APIRouter(prefix="/plan", tags=["Replanning"])
logger = logging.getLogger("uvicorn.error")


@router.post("/replan", response_model=ReplanResponse)
async def replan_trip(payload: ReplanRequest, request: Request):
    started = getattr(request.state, "started_at", perf_counter())
    fetch_start = perf_counter()
    legs, sources = await fetch_travel_data(payload)
    fetched = perf_counter()
    result = await asyncio.to_thread(replan, payload, legs)
    computed = perf_counter()
    result["data_sources"] = sources
    result["timings"] = {
        "data_fetch_ms": round((fetched-fetch_start)*1000, 3),
        "replanning_compute_ms": round((computed-fetched)*1000, 3),
        "end_to_end_ms": round((computed-started)*1000, 3),
    }
    logger.info("replan status=%s states=%s timings=%s", result["status"], result["evaluated_states"], result["timings"])
    return result
