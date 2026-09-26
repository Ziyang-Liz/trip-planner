"""Live smoke check for registered APIs; start uvicorn before running."""
import argparse
import json
import sys
from pathlib import Path
import httpx
from core.replanning_models import ReplanResponse

def run(base_url="http://127.0.0.1:8000"):
    try:
        sample = json.loads((Path(__file__).parent / "examples/replan_request.json").read_text(encoding="utf-8"))
        with httpx.Client(base_url=base_url, timeout=45, trust_env=False) as client:
            health = client.get("/")
            health.raise_for_status()
            assert health.json()["ok"] is True
            assert client.get("/plan/").status_code == 422
            response = client.post("/plan/replan", json=sample)
            response.raise_for_status()
            result = ReplanResponse.model_validate(response.json())
            assert len(result.alternatives) == 3
            assert result.timings.end_to_end_ms >= result.timings.replanning_compute_ms
        print("PASS: health, existing plan validation, replanning response and three alternatives")
        print("Data sources:", result.data_sources)
        print("Timings (ms):", result.timings.model_dump())
    except Exception as e:
        print("FAIL: Exception occurred:", repr(e))
        sys.exit(1)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    run(parser.parse_args().base_url)
