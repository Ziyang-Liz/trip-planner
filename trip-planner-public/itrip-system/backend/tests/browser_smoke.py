"""Optional headless Chrome/Edge flow test. Uses fixture travel, not real traffic.

Run from backend: python -B tests/browser_smoke.py --node PATH_TO_NODE_20
No browser automation package is needed; CDP uses the existing websockets package.
"""
import argparse
import asyncio
import base64
import json
import os
from pathlib import Path
import shutil
import socket
import subprocess
import sys
import tempfile
import time

import httpx
from websockets.asyncio.client import connect

BACKEND = Path(__file__).resolve().parents[1]
FRONTEND = BACKEND.parent / "frontend"


def fixture_app():
    from main import app
    import routers.replan

    async def fixture_travel(req):
        keys = ["@current"] + ["place:" + p.id for p in [a.place for a in req.activities] + req.candidates]
        legs = {(a, b): {"minutes": 0 if a == b else 12, "distance_km": 0 if a == b else 4,
                        "source": "browser_fixture", "verified": False} for a in keys for b in keys}
        return legs, {"travel": "browser_fixture", "cache_write": "disabled_for_test"}

    routers.replan.fetch_travel_data = fixture_travel
    return app


def free_port():
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def wait_http(url, process):
    with httpx.Client(timeout=1, trust_env=False) as client:
        for _ in range(100):
            if process.poll() is not None:
                raise RuntimeError(f"Test process exited: {process.returncode}")
            try:
                response = client.get(url)
                if response.status_code == 200:
                    return response.json() if "json" in response.headers.get("content-type", "") else None
            except httpx.TransportError:
                pass
            time.sleep(.1)
    raise RuntimeError(f"Timed out waiting for {url}")


async def browser_flow(ws_url, url, screenshots=None):
    async with connect(ws_url, max_size=8_000_000, proxy=None) as ws:
        counter, errors = 0, []

        async def command(method, params=None):
            nonlocal counter
            counter += 1
            await ws.send(json.dumps({"id": counter, "method": method, "params": params or {}}))
            while True:
                msg = json.loads(await ws.recv())
                if msg.get("method") == "Runtime.exceptionThrown":
                    errors.append(msg["params"])
                if msg.get("id") == counter:
                    if "error" in msg:
                        raise RuntimeError(msg["error"])
                    return msg.get("result", {})

        async def evaluate(expression):
            result = await command("Runtime.evaluate", {"expression": expression, "returnByValue": True, "awaitPromise": True})
            if result.get("exceptionDetails"):
                raise RuntimeError(result["exceptionDetails"])
            return result.get("result", {}).get("value")

        async def until(expression):
            for _ in range(100):
                if await evaluate(expression):
                    return
                await asyncio.sleep(.1)
            raise AssertionError(await evaluate("document.body.innerText"))

        await command("Runtime.enable")
        await command("Page.enable")
        await command("Emulation.setDeviceMetricsOverride", {"width": 1440, "height": 1000, "deviceScaleFactor": 1, "mobile": False})

        async def screenshot(name):
            if screenshots:
                screenshots.mkdir(parents=True, exist_ok=True)
                await evaluate("document.fonts.ready")
                result = await command("Page.captureScreenshot", {"format": "png"})
                (screenshots / name).write_bytes(base64.b64decode(result["data"]))

        await command("Page.navigate", {"url": url})
        await until("document.readyState === 'complete' && !!document.querySelector('.generate-btn')")
        await screenshot("homepage.png")
        sys.path.insert(0, str(BACKEND))
        from data.seed_places import get_seed_places
        pois = [dict(p, duration=1) for p in get_seed_places('Brisbane')[:8]]
        demo_weather = {"date": "Day 1", "source": "demo", "temp": 25, "weather": "clear sky", "rain_probability": 10}
        plan = {"origin": "Brisbane", "destination": "Brisbane", "days": 1, "budget": 800, "places": pois,
                "daily_plan": [{"day": 1, "date": "2026-10-01", "weather": demo_weather, "activities": pois[:3]}], "weather": [demo_weather]}
        await evaluate(f"localStorage.setItem('trip_result', {json.dumps(json.dumps(plan))}); localStorage.setItem('trip_search', '{{\"startDate\":\"2026-10-01\"}}'); location.href='/planner';")
        await until("!!document.querySelector('.replan-panel form')")
        assert await evaluate("document.querySelector('.summary-grid').innerText.includes('Demo weather')")
        assert await evaluate("document.querySelector('.weather-box').innerText.includes('Demo weather')")
        assert await evaluate("document.querySelector('.weather-card').innerText.includes('Demo weather')")
        await screenshot("planner-demo.png")
        print("PASS browser: demo weather labelled in summary, itinerary, and forecast", flush=True)
        await evaluate("document.querySelector('.replan-panel input[type=checkbox][required]').click(); document.querySelector('.replan-panel form').requestSubmit();")
        await until("document.querySelectorAll('.alternatives article').length === 3")
        assert await evaluate("document.querySelector('.replan-panel').innerText.includes('条件可行')")
        assert await evaluate("document.querySelectorAll('.change').length === 9")
        print("PASS browser: late departure, three comparisons, differences, unverified labels", flush=True)
        await evaluate("""window.setField = (text, value) => {
          const label = [...document.querySelectorAll('.replan-panel .fields label')].find(x => x.textContent.trim().startsWith(text));
          const input = label.querySelector('input,select'); input.value = value;
          input.dispatchEvent(new Event('input', {bubbles:true})); input.dispatchEvent(new Event('change', {bubbles:true}));
        }; setField('事件', 'rain');""")
        await asyncio.sleep(.1)
        await evaluate("setField('降雨开始','2026-10-01T09:00'); setField('降雨结束','2026-10-01T20:00'); [...document.querySelectorAll('.replan-panel tbody tr:first-child label')].find(x => x.textContent.includes('固定预约')).querySelector('input').click(); document.querySelector('.replan-panel form').requestSubmit();")
        await until("document.querySelector('.replan-panel').innerText.includes('所提供数据的硬约束下无可行方案') && !document.querySelector('.alternatives article')")
        print("PASS browser: rain plus fixed outdoor booking rejected", flush=True)
        await evaluate("setField('当前时间','2026-10-01T11:00'); [...document.querySelectorAll('.replan-panel tbody tr:first-child label')].find(x => x.textContent.includes('固定预约')).querySelector('input').click(); [...document.querySelectorAll('.replan-panel tbody tr:first-child label')].find(x => x.textContent.includes('已完成')).querySelector('input').click(); document.querySelector('.replan-panel form').requestSubmit();")
        await until("document.querySelectorAll('.alternatives article').length === 3")
        assert await evaluate("document.querySelector('.alternatives').innerText.includes('已完成，不变')")
        assert not errors, errors
        print("PASS browser: completed activity preserved; no uncaught application errors", flush=True)
        await command("Browser.close")


def run():
    parser = argparse.ArgumentParser()
    parser.add_argument("--node", default=shutil.which("node"))
    parser.add_argument("--browser", default="C:/Program Files/Google/Chrome/Application/chrome.exe")
    parser.add_argument("--screenshots", type=Path, help="Optional directory for documentation screenshots")
    args = parser.parse_args()
    if not args.node or not Path(args.browser).exists():
        raise SystemExit("Supply --node and --browser executable paths.")
    api_port, ui_port, debug_port = free_port(), free_port(), free_port()
    processes = []
    env = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1"}
    with tempfile.TemporaryDirectory(prefix="itrip-browser-test-") as profile:
        try:
            api = subprocess.Popen([sys.executable, '-B', '-c', f"import sys; sys.path.insert(0,'tests'); import uvicorn; from browser_smoke import fixture_app; uvicorn.run(fixture_app(), host='127.0.0.1', port={api_port}, log_level='warning')"], cwd=BACKEND, env=env)
            processes.append(api)
            wait_http(f"http://127.0.0.1:{api_port}/", api)
            js = f"import {{createServer}} from 'vite'; const server=await createServer({{server:{{host:'127.0.0.1',port:{ui_port},strictPort:true,proxy:{{'^/plan(?:/|$)':{{target:'http://127.0.0.1:{api_port}',changeOrigin:true}}}}}}}}); await server.listen();"
            vite = subprocess.Popen([args.node, '--input-type=module', '-e', js], cwd=FRONTEND, env=env)
            processes.append(vite)
            wait_http(f"http://127.0.0.1:{ui_port}/", vite)
            browser = subprocess.Popen([args.browser, '--headless=new', '--no-first-run', '--no-default-browser-check', f'--remote-debugging-port={debug_port}', f'--user-data-dir={profile}', 'about:blank'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            processes.append(browser)
            pages = wait_http(f"http://127.0.0.1:{debug_port}/json", browser)
            target = next(p for p in pages if p['type'] == 'page')
            asyncio.run(browser_flow(target['webSocketDebuggerUrl'], f"http://127.0.0.1:{ui_port}/", args.screenshots))
        finally:
            for process in reversed(processes):
                if process.poll() is None:
                    process.terminate()
                process.wait(timeout=10)


if __name__ == '__main__':
    run()
