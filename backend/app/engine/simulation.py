"""Real-time simulation loop that moves drones along their planned paths."""

from __future__ import annotations

import asyncio
import json
import logging
import math
from dataclasses import dataclass, field

from app.engine.benchmark import benchmark
from app.engine.physics import (
    BatteryState,
    WindCondition,
    DRONE_SPEED_KMH,
    compute_heading,
    effective_speed,
)
from app.engine.routing import compute_battery_cost, haversine_km, GridNode

logger = logging.getLogger("drone_delivery.simulation")


@dataclass
class SimDrone:
    drone_id: int
    lat: float
    lon: float
    battery: BatteryState
    payload_kg: float
    path: list[list[float]] = field(default_factory=list)
    path_index: int = 0
    status: str = "idle"
    order_id: int | None = None
    home_lat: float = 0.0
    home_lon: float = 0.0
    returning_to_base: bool = False


class SimulationEngine:
    def __init__(self, tick_seconds: float = 1.0):
        self.tick_seconds = tick_seconds
        self.drones: dict[int, SimDrone] = {}
        self.wind = WindCondition()
        self._running = False
        self._subscribers: list[asyncio.Queue] = []

    def subscribe(self) -> asyncio.Queue:
        q: asyncio.Queue = asyncio.Queue(maxsize=100)
        self._subscribers.append(q)
        return q

    def unsubscribe(self, q: asyncio.Queue) -> None:
        if q in self._subscribers:
            self._subscribers.remove(q)

    def add_drone(self, sim_drone: SimDrone) -> None:
        self.drones[sim_drone.drone_id] = sim_drone

    def assign_path(self, drone_id: int, path: list[list[float]], order_id: int | None = None) -> None:
        drone = self.drones.get(drone_id)
        if not drone:
            return
        drone.path = path
        drone.path_index = 0
        drone.status = "en_route"
        drone.order_id = order_id
        drone.returning_to_base = False

    def set_wind(self, speed_kmh: float, direction_deg: float) -> None:
        self.wind = WindCondition(speed_kmh=speed_kmh, direction_deg=direction_deg)

    async def run(self) -> None:
        self._running = True
        while self._running:
            self._tick()
            state = self._snapshot()
            for q in list(self._subscribers):
                try:
                    q.put_nowait(state)
                except asyncio.QueueFull:
                    pass
            await asyncio.sleep(self.tick_seconds)

    def stop(self) -> None:
        self._running = False

    def _tick(self) -> None:
        with benchmark("simulation_tick", collect=len(self.drones) > 0):
            self._advance_drones()

    def _advance_drones(self) -> None:
        for drone in self.drones.values():
            if drone.status != "en_route" or not drone.path:
                continue

            if drone.path_index >= len(drone.path) - 1:
                drone.status = "idle" if not drone.returning_to_base else "charging"
                drone.path = []
                drone.path_index = 0
                if drone.returning_to_base:
                    drone.battery.current_pct = min(100.0, drone.battery.current_pct)
                    drone.returning_to_base = False
                continue

            target = drone.path[drone.path_index + 1]
            heading = compute_heading(drone.lat, drone.lon, target[0], target[1])
            speed = effective_speed(DRONE_SPEED_KMH, self.wind, heading)
            dist_per_tick = (speed / 3600.0) * self.tick_seconds

            remaining = haversine_km(
                GridNode(drone.lat, drone.lon),
                GridNode(target[0], target[1]),
            )

            if dist_per_tick >= remaining:
                drone.lat = target[0]
                drone.lon = target[1]
                drone.path_index += 1
                seg_dist = remaining
            else:
                frac = dist_per_tick / remaining if remaining > 0 else 0
                drone.lat += (target[0] - drone.lat) * frac
                drone.lon += (target[1] - drone.lon) * frac
                seg_dist = dist_per_tick

            cost = compute_battery_cost(
                seg_dist, drone.payload_kg, drone.battery.capacity_mah, self.wind.vector
            )
            drone.battery.drain(cost)

            if drone.battery.needs_return and not drone.returning_to_base:
                drone.returning_to_base = True
                drone.status = "en_route"

    def _snapshot(self) -> dict:
        return {
            "type": "sim_update",
            "wind": {"speed_kmh": self.wind.speed_kmh, "direction_deg": self.wind.direction_deg},
            "drones": [
                {
                    "drone_id": d.drone_id,
                    "lat": round(d.lat, 6),
                    "lon": round(d.lon, 6),
                    "battery_pct": round(d.battery.current_pct, 1),
                    "status": d.status,
                    "order_id": d.order_id,
                    "returning_to_base": d.returning_to_base,
                    "path": d.path,
                    "path_index": d.path_index,
                }
                for d in self.drones.values()
            ],
        }


simulation_engine = SimulationEngine()
