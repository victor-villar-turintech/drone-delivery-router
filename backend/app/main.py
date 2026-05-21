import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import engine, Base
from app.engine.simulation import simulation_engine
from app.routers import drones, orders, hubs, nofly_zones, simulation


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    simulation_engine.tick_seconds = settings.sim_tick_seconds
    sim_task = asyncio.create_task(simulation_engine.run())
    yield
    simulation_engine.stop()
    sim_task.cancel()
    try:
        await sim_task
    except asyncio.CancelledError:
        pass


app = FastAPI(
    title="Drone Delivery Router",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(drones.router)
app.include_router(orders.router)
app.include_router(hubs.router)
app.include_router(nofly_zones.router)
app.include_router(simulation.router)


@app.get("/health")
async def health():
    return {"status": "ok"}
