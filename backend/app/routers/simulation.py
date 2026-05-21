import asyncio
import json

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from pydantic import BaseModel

from app.engine.simulation import simulation_engine
from app.websocket.manager import ws_manager

router = APIRouter(tags=["simulation"])


class WindUpdate(BaseModel):
    speed_kmh: float
    direction_deg: float


@router.post("/api/simulation/wind")
async def set_wind(body: WindUpdate):
    simulation_engine.set_wind(body.speed_kmh, body.direction_deg)
    return {"status": "ok", "wind": {"speed_kmh": body.speed_kmh, "direction_deg": body.direction_deg}}


@router.get("/api/simulation/state")
async def get_state():
    return simulation_engine._snapshot()


@router.websocket("/ws/simulation")
async def ws_simulation(ws: WebSocket):
    await ws_manager.connect(ws)
    queue = simulation_engine.subscribe()
    try:
        while True:
            state = await queue.get()
            await ws.send_text(json.dumps(state))
    except WebSocketDisconnect:
        pass
    finally:
        simulation_engine.unsubscribe(queue)
        ws_manager.disconnect(ws)
