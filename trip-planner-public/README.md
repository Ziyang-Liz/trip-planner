# Intelligent Trip Planning System

A Vue + Vite frontend, FastAPI backend, PostgreSQL database, and OpenTripMap / OpenWeather APIs.
The main feature generates daily recommendations based on attractions, weather, budget, and preferences. A second workflow adjusts an existing day after rain or a late departure, while respecting completed activities, fixed appointments, and known costs.

This is a local development and demonstration project extracted from an existing project. See [project origin and data sources](ATTRIBUTIONS.md).

## Screenshots

Search and preferences:

![Trip search page](docs/images/homepage.png)

Results and disruption replanning, captured with curated test attractions and explicitly labelled demo weather:

![Results page showing demo weather](docs/images/planner-demo.png)

## Development Environment Baseline

- Windows x64, Python 3.12 (locally verified with 3.12.10).
- Node.js 20.19.x or a later 20.x version, and npm 10.x (the build was verified with a temporary Node 20.19.0 installation). Some locked dependencies require Node >=20.19.0; even if 20.17.0 can build the project, it does not meet all dependency requirements.
- Docker Desktop and Docker Compose v2 are required to run the database provided by this repository.
- The backend `requirements.lock` pins runtime dependencies for Windows / Python 3.12; the frontend uses `package-lock.json` and `npm ci`.
- Do not copy `.venv` or `node_modules` from another computer; follow the installation steps below for a fresh checkout.

The commands below use PowerShell. Run the initial setup commands from the repository root.

## 1. Configure Environment Variables

```powershell
if (!(Test-Path itrip-system/backend/.env)) {
    Copy-Item itrip-system/backend/.env.example itrip-system/backend/.env
}
```

Edit `itrip-system/backend/.env`. Preserve and review any existing `.env` instead of overwriting it.

| Variable | Purpose |
| --- | --- |
| `PG_HOST` | Database address used by the local backend; use `127.0.0.1` for local Compose setup |
| `PG_PORT` | Local database port, defaulting to `5432`; Compose maps to the same value |
| `PG_DB` / `PG_USER` / `PG_PASSWORD` | Database name, username, and password shared by both backend database clients and Compose |
| `PG_CONNECT_TIMEOUT` | Database connection timeout in seconds, defaulting to `5` |
| `OPENTRIPMAP_API_KEY` | Required to fetch attractions when the main endpoint has a cache miss |
| `OPENWEATHER_API_KEY` | Retrieves real weather; the current implementation returns demo weather when absent |

The template defaults to `trip_db / postgres / postgres` for local development.
The backend loads configuration from the fixed `backend/.env` path; existing process environment variables take precedence.
Compose commands must explicitly pass the same file using `--env-file`. Restart the backend after changing configuration.
Passwords containing `$` or `#` can be enclosed in single quotes in `.env`. Keep API keys only in the backend.

## 2. Start the Database

```powershell
docker compose --env-file itrip-system/backend/.env -f itrip-system/infra/docker-compose.yml config --quiet
docker compose --env-file itrip-system/backend/.env -f itrip-system/infra/docker-compose.yml up -d --wait db
docker compose --env-file itrip-system/backend/.env -f itrip-system/infra/docker-compose.yml ps
```

The database port binds only to the local machine. If PostgreSQL is already installed locally, configure it in `.env` and skip starting the container.
If `5432` is already in use, use the existing database or change `PG_PORT` in `.env`.

Optional pgAdmin:

```powershell
docker compose --env-file itrip-system/backend/.env -f itrip-system/infra/docker-compose.yml --profile tools up -d --wait
```

Visit `http://localhost:5050`. Login credentials are set by `PGADMIN_DEFAULT_EMAIL` / `PGADMIN_DEFAULT_PASSWORD`.
When connecting to the database in pgAdmin, use `db` as the host, `5432` as the port, and the `PG_*` values for credentials and the database name.

The `dbdata` volume stores database data. Initialization SQL runs only on the first startup with an empty data volume; changing `.env` does not update credentials in an existing database.
Stop services with `docker compose --env-file itrip-system/backend/.env -f itrip-system/infra/docker-compose.yml --profile tools down`; this command preserves the data volume.

## 3. Install and Start the Backend

```powershell
cd itrip-system/backend
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.lock
.\.venv\Scripts\python.exe -m pip check
.\.venv\Scripts\python.exe -m uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

Skip virtual environment creation if a working `.venv` already exists. If the Windows `py` launcher is unavailable, use `python -m venv .venv` after confirming the Python version.
Run directly from the backend directory; an editable installation is not required. `pyproject.toml` also records direct dependency versions.

- Liveness check: `http://127.0.0.1:8000/`
- API documentation: `http://127.0.0.1:8000/docs`
- Main endpoint: `GET /plan/?origin=Brisbane&destination=Brisbane&days=3&budget=800&preference=Nature`

A successful liveness check only means the application has started; it does not confirm that the database, API keys, and third-party services are available.

## 4. Install and Start the Frontend

Open another terminal and run from the repository root:

```powershell
cd itrip-system/frontend
npm.cmd ci
npm.cmd run dev
```

Open the address printed by Vite; the configured port is `5173`. The development proxy forwards requests such as `/plan` to `http://127.0.0.1:8000`.
The frontend requires no `.env` or API keys. A copied frontend `.env` is local configuration and is excluded from public exports. Build with `npm.cmd run build`.
`npm.cmd run preview` only previews the build output; production deployment requires additional API reverse proxy configuration and a fallback for Vue history routing.

## Verification

From the backend directory:

```powershell
.\.venv\Scripts\python.exe -B -m unittest discover -s tests -v
.\.venv\Scripts\python.exe -m pip check
```

From the frontend directory:

```powershell
npm.cmd run build
```

`tests/` includes the original algorithm tests and tests for replanning constraints, endpoints, and cache degradation. These do not depend on real external APIs or a database.
After starting the backend, run `python -B test_api.py` to check actual HTTP requests, parameter validation for the original `/plan/` endpoint, and the replanning endpoint.
Optional browser workflow check: `python -B tests/browser_smoke.py` (requires local Chrome and Node 20.19+; accepts `--browser` / `--node`). It starts the backend and frontend on separate ports, uses fixed transport test data, and verifies late departure, conflicts between rain and fixed appointments, preservation of completed activities, and plan comparison. It shuts down the processes afterward.
The browser check also verifies demo weather labels. Add `--screenshots ../../docs/images` to regenerate the documentation screenshots from the backend directory.
A Vite build does not perform full TypeScript type checking; the project still has no full type-checking script configured.

## Disruption Replanning: First Version

The backend adds `POST /plan/replan` while maintaining compatibility with the original `GET /plan/`. In the existing results page's "Disruptions: Minimal-Change Replanning" panel:

1. Select a day to adjust and check the date, original activity start and end times, and current location. The original plan has no schedule; the page generates an editable draft starting at 09:00.
2. Mark completed activities, must-visit activities, and fixed appointments; add confirmed opening windows, visit durations, costs, and cancellation fees. Missing information can be left blank and will be listed as "unverified" in the response.
3. Select a late departure (for example, 40 minutes) or a rain period, then enter the deadline and total budget. Include costs for other days, accommodation, meals, and similar commitments under "Other Committed Costs" without counting the current activities' costs twice.
4. Generate and compare plans for three objectives. Review each activity's retained / moved / replaced / removed status, reasons, costs, times, and the updated attraction map. Map lines are illustrative only.

### Request and Constraint Semantics

See `itrip-system/backend/examples/replan_request.json` for a complete request example. Field constraints are also available at `/docs`.
The example attractions come from the existing Brisbane seed pool; dates, time slots, and visit durations are demo inputs, and costs are estimates. They do not represent verified bookings or opening information.
This candidate pool can verify the complete replanning workflow without first calling the attractions API. After starting the service in the backend directory, open another terminal:

```powershell
# Run in itrip-system/backend
$replanBody = Get-Content -Raw -Encoding UTF8 examples/replan_request.json
Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8000/plan/replan -ContentType 'application/json; charset=utf-8' -Body ([System.Text.Encoding]::UTF8.GetBytes($replanBody))
```

- Times must include a timezone; the frontend accepts times in the browser's local timezone and converts them to UTC. The API supports up to 8 activities, 20 candidates, and a bounded time window of up to 7 days. The first frontend version adjusts one day at a time and leaves other days unchanged.
- All amounts use the same currency unit and allow at most two decimal places to prevent rounding from hiding budget overruns.
- Activity IDs identify individual visits, while place IDs identify POIs. Metadata for the same place ID must be consistent. The original candidate pool is a request snapshot; no random generation or additional place searches are performed.
- Completed activities must end before the current time and are returned unchanged. `must_visit` prevents removal / replacement; `fixed_time` or `locked_activity_ids` also prevent rescheduling.
- For late departures, the earliest departure time is `max(current_time, planned_departure + delay_minutes)`; the delay is not added repeatedly.
- Known outdoor activities are prohibited during rain windows; they can be moved until after the rain or replaced with other activities from the candidate pool. Indoor / outdoor labels based only on inference remain marked as unverified.
- For opening windows, `null` means unknown, `[]` means closed throughout the time window, and a nonempty list contains confirmed opening periods supplied by the user. The `*_verified` flags for visit duration and price default to false; estimates from the original endpoint are not automatically treated as facts.
- The total budget includes completed activities, the current remaining activities, known cancellation fees, other committed costs, and fixed transport costs. `transport_cost` applies only to a fixed cost covering all candidate routes (such as a day pass); leave it blank when distance-based fares are unknown. Cancellation fees count only when activities are removed / replaced. Unknown items are not treated as fully known zero costs; the response returns a known subtotal, indicates that the full cost is unavailable, and includes unverified-data notices.
- Three plans are not fabricated when there are too few candidates. Itineraries that violate known hard constraints are not returned; missing required transport / visit duration data produces `insufficient_data`.

### Search, Data, and Experiment Timing

The search prioritizes local adjustments to the original activities, allowing waiting, reordering, replacement, and removal of unprotected activities. The three objectives are ranked separately, favoring different activity combinations or orders and removing duplicate plans.
Cost ranking prioritizes candidates with complete data, then compares known costs; a true minimum cost cannot be claimed when costs are unknown.
The algorithm uses bounded multi-objective beam search (width 60, at most 100,000 candidate evaluations) and does not guarantee a global optimum. `search_truncated` explicitly reports pruning; if a limited search finds no results, it returns `search_limit` without claiming mathematical infeasibility. At least one unfinished activity must be retained; if all activities are completed, only the original itinerary may be returned.

Transport data reuses the asynchronous client in `services/osrm.py` to fetch directed driving-time matrices in batches, along with the existing PostgreSQL API cache (15 minutes) and an in-process TTL cache. Synchronous database operations run in worker threads without blocking the asynchronous request thread.
If OSRM fails, straight-line distance and 25 km/h are used as an explicit estimate, which is not cached as real road data. Missing coordinates are not assumed to imply zero travel time. OSRM itself does not provide live traffic, so time constraints remain marked as unverified.

Responses include `data_fetch_ms`, `replanning_compute_ms`, and `end_to_end_ms`; server logs also record status, the number of search states, and these durations. End-to-end timing starts when the server receives the request. The timing in the response body ends when computation finishes; the `X-End-To-End-Ms` response header additionally includes response serialization, but excludes the client's network round trip. The page displays browser round-trip time separately.
The three objectives use the same data snapshot for comparison. Fixed transport test data is injected only into test processes; the production endpoint does not accept fabricated transport matrices from clients.

### Cache Table Initialization

`db/schema.sql` now includes idempotent creation of `public.api_cache` and its expiration index. It runs when a new Docker data volume starts for the first time.
Existing databases do not automatically run the added SQL; apply it manually (the example below uses the template's default database name and username; replace them with your local configuration):

```powershell
psql -h 127.0.0.1 -U postgres -d trip_db -v ON_ERROR_STOP=1 -f itrip-system/db/schema.sql
```

Run this command from the repository root. It does not delete tables or existing records. If initialization has not been performed or the database is unreachable, caching degrades gracefully; `data_sources` in the response shows the transport source and cache write status, while core replanning remains available.

## Current Baseline Limitations

- The legacy history tables have not yet been unified with the ORM history models, and the `/demo` route is not enabled. This iteration adds no booking or itinerary history writes.
- The original `GET /plan/` still provides coarse recommendations based on day count and scores; only the new replanning endpoint uses explicit schedules and cumulative cost validation.
- Live traffic, official opening hours, live ticket prices, and cancellation policies are not yet integrated. Plans with unknown constraints are marked `conditional` and cannot be treated as confirmed feasible itineraries.
- Locally curated attractions are not a fallback for failed OpenTripMap requests; itinerary generation requires a valid key and network access.
- Application dependencies are pinned at this stage. Docker images still use the `postgres:16` and `dpage/pgadmin4:8` tags; image digests are not yet pinned.

## Directory Structure and Version Control

```text
itrip-system/
  backend/       FastAPI, services, configuration, tests, and dependency lockfile
  frontend/      Vue pages, Leaflet maps, and Vite configuration
  db/            Existing initialization SQL
  infra/         Docker Compose
```

Commit source code, dependency manifests, lockfiles, and `.env.example`; do not commit `.env`, virtual environments, `node_modules`, bytecode, or build artifacts.
When upgrading dependencies, update both direct dependencies and lockfiles, then rerun installation, tests, and build checks.

## Public source export

From the repository root, run:

```powershell
python scripts/export_public.py
```

This creates a timestamped source ZIP under `release/`. Extract it into a new folder before creating your public GitHub repository; upload the extracted source files. It excludes real `.env` files, virtual environments, `node_modules`, bytecode, editor settings, generated metadata, build output, and local tools. `.env.example` and dependency lockfiles are included. The exporter also rejects source files containing long credential values found in the local environment files; this is an additional check, not a complete secret scanner.

Local credentials and dependencies remain on your computer so your development environment can keep working. Do not upload this entire working folder as a ZIP. The export does not include Git history.

## API failures and weather sources

`GET /plan/` returns a JSON `detail` message for missing attraction configuration (503), upstream failures or invalid JSON (502), timeouts (504), and an unknown city or blank city input (422). The frontend displays the message. Upstream diagnostics record the service name, exception type, and HTTP status only; request URLs, response bodies, and credentials are omitted.

Each weather item includes `source`: `openweather`, `openweather_cache`, or `demo`. Days beyond the returned forecast have `source: unavailable` in `daily_plan` and null weather measurements. Demo weather is labelled in the results page and weather advice; older saved results without source metadata are labelled unverified. Demo values are repeated to cover the requested day count and do not represent a forecast. Changing the weather cache schema prevents older entries without source metadata from being presented as verified API data.

## Public hosting

The documented commands bind services to the local machine. A public source repository does not require a publicly reachable backend. Before hosting the application for public traffic, configure allowed origins, authentication or access controls, rate limits, and service credentials for that deployment. The current backend retains permissive CORS for local development.
