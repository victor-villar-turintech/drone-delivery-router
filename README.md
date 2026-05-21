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

## Running Tests

```bash
cd backend
source venv/bin/activate
pytest -v
```

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
│   │   │   └── simulation.py    # Tick-based simulation loop
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
│   │   │   └── OrderList.jsx    # Order management panel
│   │   └── hooks/
│   │       └── useWebSocket.js  # Auto-reconnecting WS hook
│   └── package.json
├── .env.example                 # Environment variable template
├── setup.sh                     # One-command local setup
└── README.md
```
