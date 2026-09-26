from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent / ".env")

from time import perf_counter
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from routers import trip, replan

app = FastAPI(title="Real-Time Trip Planner")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(trip.router)
app.include_router(replan.router)


@app.middleware("http")
async def measure_request(request: Request, call_next):
    request.state.started_at = perf_counter()
    response = await call_next(request)
    response.headers["X-End-To-End-Ms"] = f"{(perf_counter()-request.state.started_at)*1000:.3f}"
    return response


@app.get("/")
def ping():
    return {"ok": True, "service": "trip-planner"}
