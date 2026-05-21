"""Integration-style tests for the FastAPI endpoints (uses in-memory SQLite)."""

import pytest
from unittest.mock import patch, AsyncMock
from httpx import AsyncClient, ASGITransport

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from app.database import Base, get_db
from app.main import app


@pytest.fixture()
async def async_db():
    engine = create_async_engine("sqlite+aiosqlite:///", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with session_factory() as session:
        yield session
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest.fixture()
async def client(async_db):
    async def _override():
        yield async_db

    app.dependency_overrides[get_db] = _override
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_health(client):
    resp = await client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


@pytest.mark.asyncio
async def test_create_and_list_drones(client):
    payload = {
        "name": "TestDrone",
        "max_payload_kg": 5.0,
        "battery_capacity_mah": 8000,
        "battery_pct": 100.0,
        "latitude": 37.77,
        "longitude": -122.42,
    }
    resp = await client.post("/api/drones/", json=payload)
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "TestDrone"

    resp = await client.get("/api/drones/")
    assert resp.status_code == 200
    assert len(resp.json()) == 1


@pytest.mark.asyncio
async def test_create_order(client):
    payload = {
        "pickup_lat": 37.77,
        "pickup_lon": -122.42,
        "dropoff_lat": 37.78,
        "dropoff_lon": -122.41,
        "package_weight_kg": 1.5,
        "priority": "high",
    }
    resp = await client.post("/api/orders/", json=payload)
    assert resp.status_code == 201
    assert resp.json()["status"] == "pending"


@pytest.mark.asyncio
async def test_create_hub(client):
    payload = {
        "name": "Test Hub",
        "latitude": 37.77,
        "longitude": -122.42,
        "is_charging_station": True,
    }
    resp = await client.post("/api/hubs/", json=payload)
    assert resp.status_code == 201


@pytest.mark.asyncio
async def test_create_nofly_zone(client):
    payload = {
        "name": "Test Zone",
        "polygon_geojson": '{"type":"Polygon","coordinates":[[[-122.42,37.77],[-122.42,37.78],[-122.41,37.78],[-122.41,37.77],[-122.42,37.77]]]}',
    }
    resp = await client.post("/api/nofly-zones/", json=payload)
    assert resp.status_code == 201


@pytest.mark.asyncio
async def test_simulation_state(client):
    resp = await client.get("/api/simulation/state")
    assert resp.status_code == 200
    assert "drones" in resp.json()
