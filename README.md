# Drone Delivery Router

An automated drone delivery routing system that optimizes delivery paths for a fleet of drones, accounting for payload capacities, battery depletion curves, wind conditions, and dynamic no-fly zones.

## Architecture

```
┌──────────────────────────────────────────────────┐
│                React Dashboard                   │
│  (Leaflet map · fleet sidebar · order dispatch)  │
│                 :5173                            │
└──────────────┬──────────────┬────────────────────┘
               │ REST         │ WebSocket
               ▼              ▼
┌──────────────────────────────────────────────────┐
│              FastAPI Backend                      │
│  Routing Engine · Simulation Loop · Physics      │
│                 :8000                            │
└──────────────────────┬───────────────────────────┘
                       │
                       ▼
┌──────────────────────────────────────────────────┐
│         PostgreSQL + PostGIS                      │
│  Drones · Orders · Hubs · No-Fly Zones           │
│                 :5432                            │
└──────────────────────────────────────────────────┘
```

## Features

- **Fleet Management** – register drones with payload/battery specs; track status in real-time.
- **Order Dispatch** – create delivery orders with pickup/dropoff coordinates, weight, and priority.
- **A\* Pathfinding** – 2-D grid-based routing that strictly avoids no-fly zone polygons.
- **Battery Physics** – consumption scales with distance, payload weight, and headwind; auto return-to-base at 15% threshold.
- **Wind Model** – configurable wind speed/direction that dynamically adjusts route cost and drone ground speed.
- **Live Simulation** – tick-based engine streams drone telemetry over WebSocket.
- **Operator Dashboard** – Leaflet map with shaded NFZ polygons, hub markers, moving drone icons, planned-path lines, and a sidebar with fleet health + order management.

## Prerequisites

| Tool | Version |
|------|---------|
| Python | 3.11+ |
| Node.js | 18+ |
| PostgreSQL | 14+ with PostGIS |
| Homebrew | (macOS) |

## Quick Start

### 1. Configure environment

```bash
cp .env.example .env
# Edit .env with your PostgreSQL credentials
```

**Key variables in `.env`:**

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | `postgresql+asyncpg://drone_user:drone_pass@localhost:5432/drone_delivery` | Async SQLAlchemy connection string |
| `DATABASE_URL_SYNC` | `postgresql://drone_user:drone_pass@localhost:5432/drone_delivery` | Sync connection string (for scripts) |
| `BACKEND_HOST` | `0.0.0.0` | Backend bind address |
| `BACKEND_PORT` | `8000` | Backend port |
| `VITE_API_URL` | `http://localhost:8000` | Frontend → API base URL |
| `VITE_WS_URL` | `ws://localhost:8000/ws/simulation` | Frontend → WebSocket URL |
| `SIM_TICK_SECONDS` | `1.0` | Simulation tick interval |

### 2. Run the setup script

```bash
chmod +x setup.sh
./setup.sh
```

This will:
1. Install/verify Homebrew packages (PostgreSQL, PostGIS, Python 3.11, Node.js)
2. Create a Python `venv` and install backend dependencies
3. Initialize the database schema and seed San Francisco mock data
4. Install frontend `node_modules`

### 3. Start the backend

```bash
cd backend
source venv/bin/activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 4. Start the frontend

```bash
cd frontend
npm run dev
```

### 5. Open the dashboard

- **Dashboard:** http://localhost:5173
- **API docs:** http://localhost:8000/docs

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/health` | Health check |
| `GET` | `/api/drones/` | List all drones |
| `POST` | `/api/drones/` | Register a new drone |
| `GET` | `/api/orders/` | List all orders |
| `POST` | `/api/orders/` | Create a delivery order |
| `POST` | `/api/orders/{id}/dispatch` | Assign a drone and compute route |
| `GET` | `/api/hubs/` | List hub/charging stations |
| `POST` | `/api/hubs/` | Create a hub |
| `GET` | `/api/nofly-zones/` | List no-fly zones |
| `POST` | `/api/nofly-zones/` | Create a no-fly zone |
| `POST` | `/api/simulation/wind` | Update wind speed & direction |
| `GET` | `/api/simulation/state` | Get current simulation snapshot |
| `WS` | `/ws/simulation` | Live simulation telemetry stream |
| `GET` | `/api/benchmark/stats` | Accumulated benchmark metrics for all instrumented functions |
| `POST` | `/api/benchmark/routing` | Run routing benchmark (query param: `iterations`, default 5) |
| `POST` | `/api/benchmark/physics` | Run physics benchmark (query param: `iterations`, default 1000) |

## Running Tests

```bash
cd backend
source venv/bin/activate
pytest -v
```

## Performance Benchmarking

The system includes built-in benchmarking for both backend and frontend.

### Backend Benchmarks

Backend benchmarks measure **wall-clock time**, **CPU user/system time**, **peak RSS memory**, and **RSS delta** for every instrumented operation. Metrics are automatically logged to the server console and aggregated across calls.

**Automatic instrumentation** — once the backend is running, the following operations are benchmarked on every invocation:
- `find_path()` — A* pathfinding (logged per call)
- `simulation_tick` — each simulation tick
- `dispatch_order()` — full dispatch pipeline (also returned in the API response)

You will see `[BENCH]` log lines in the server console:

```
18:04:12 INFO [drone_delivery.benchmark] [BENCH] find_path        wall=  12.34 ms  cpu_user=  11.80 ms  cpu_sys=   0.42 ms  peak_rss=98304 KB  rss_delta=+128 KB
```

**On-demand benchmark endpoints:**

```bash
# Run routing benchmark (A* pathfinding, 5 iterations)
curl -X POST "http://localhost:8000/api/benchmark/routing?iterations=5"

# Run physics benchmark (battery/wind computations, 1000 iterations)
curl -X POST "http://localhost:8000/api/benchmark/physics?iterations=1000"

# View accumulated stats for all instrumented functions
curl http://localhost:8000/api/benchmark/stats
```

Example routing benchmark response:

```json
{
  "benchmark": {
    "name": "find_path",
    "count": 5,
    "wall_time_ms": { "mean": 1.6, "median": 1.7, "min": 1.3, "max": 1.8, "stdev": 0.23 },
    "cpu_total_ms": { "mean": 1.6, "median": 1.5, "min": 1.3, "max": 1.7 },
    "peak_rss_kb": 91960
  },
  "route_sample": { "path": [...], "distance_km": 1.42, "battery_cost_pct": 3.26 }
}
```

You can also use the benchmark utilities programmatically in Python:

```python
from app.engine.benchmark import benchmark, benchmark_fn, run_routing_benchmark

# As a context manager
with benchmark("my_operation") as result:
    do_something()
print(result.wall_time_ms, result.cpu_user_ms, result.peak_rss_kb)

# As a decorator
@benchmark_fn("my_function")
def my_function():
    ...
```

### Frontend Benchmarks

Frontend benchmarks run automatically in the browser and track:
- **FPS** — frames per second
- **JS Heap Memory** — used and total heap size (Chrome only)
- **WebSocket Latency** — processing time per incoming simulation message
- **Web Vitals** — FCP, LCP, CLS, INP, TTFB (via the `web-vitals` library)
- **React Render Times** — per-component render duration via React Profiler

**Dashboard panel:** Open the dashboard at `http://localhost:5173`, scroll to the bottom of the sidebar, and click **"Performance ▸"** to expand the live metrics panel.

**Browser console:** Open DevTools (F12) → Console to see `[BENCH-FRONTEND]` log entries emitted every 5 seconds:

```
[BENCH-FRONTEND] {
  fps: 61,
  renders: { Sidebar: { count: 100, avgMs: 0.6, maxMs: 2.1 }, MapView: { ... } },
  wsLatency: { count: 74, avgMs: 0.08, maxMs: 0.2 },
  webVitals: { TTFB: 9, FCP: 148, LCP: 200 },
  memory: { usedMB: 14, totalMB: 15, limitMB: 2144 }
}
```

> **Note:** `performance.memory` (JS Heap) is only available in Chromium-based browsers. Web Vitals are one-shot metrics captured on page load.

## Project Structure

```
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI application entry point
│   │   ├── config.py            # Pydantic settings
│   │   ├── database.py          # SQLAlchemy async engine
│   │   ├── models/              # ORM models (Drone, Order, Hub, NoFlyZone)
│   │   ├── schemas/             # Pydantic request/response schemas
│   │   ├── routers/             # API route handlers
│   │   ├── engine/
│   │   │   ├── routing.py       # A* pathfinding with NFZ avoidance
│   │   │   ├── physics.py       # Battery depletion & wind model
│   │   │   ├── simulation.py    # Tick-based simulation loop
│   │   │   └── benchmark.py     # Performance benchmarking utilities
│   │   └── websocket/
│   │       └── manager.py       # WebSocket connection manager
│   ├── sql/
│   │   ├── 001_schema.sql       # Database schema (PostGIS)
│   │   └── 002_seed.sql         # San Francisco seed data
│   ├── tests/                   # Pytest test suite
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── App.jsx              # Root component
│   │   ├── components/
│   │   │   ├── MapView.jsx      # Leaflet map with drones, NFZs, hubs
│   │   │   ├── Sidebar.jsx      # Dashboard sidebar
│   │   │   ├── DroneList.jsx    # Fleet health panel
│   │   │   ├── OrderList.jsx    # Order management panel
│   │   │   └── BenchmarkPanel.jsx # Live performance metrics overlay
│   │   └── hooks/
│   │       ├── useWebSocket.js  # Auto-reconnecting WS hook
│   │       └── useBenchmark.js  # Frontend performance measurement
│   └── package.json
├── .env.example                 # Environment variable template
├── setup.sh                     # One-command local setup
└── README.md
```
