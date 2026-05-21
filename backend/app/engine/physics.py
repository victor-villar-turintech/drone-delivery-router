"""Battery depletion model and wind physics for drone routing."""

from __future__ import annotations

import math
from dataclasses import dataclass


@dataclass
class WindCondition:
    speed_kmh: float = 0.0
    direction_deg: float = 0.0

    @property
    def vector(self) -> tuple[float, float]:
        rad = math.radians(self.direction_deg)
        return (
            self.speed_kmh * math.cos(rad),
            self.speed_kmh * math.sin(rad),
        )


@dataclass
class BatteryState:
    capacity_mah: int
    current_pct: float

    @property
    def remaining_mah(self) -> float:
        return self.capacity_mah * (self.current_pct / 100.0)

    def drain(self, pct: float) -> None:
        self.current_pct = max(0.0, self.current_pct - pct)

    @property
    def needs_return(self) -> bool:
        return self.current_pct <= 15.0


DRONE_SPEED_KMH = 60.0
BATTERY_RETURN_THRESHOLD = 15.0


def effective_speed(base_speed: float, wind: WindCondition, heading_deg: float) -> float:
    heading_rad = math.radians(heading_deg)
    wind_rad = math.radians(wind.direction_deg)
    relative_angle = heading_rad - wind_rad
    headwind_component = wind.speed_kmh * math.cos(relative_angle)
    return max(base_speed - headwind_component, base_speed * 0.3)


def estimate_flight_time_hours(distance_km: float, wind: WindCondition, heading_deg: float) -> float:
    speed = effective_speed(DRONE_SPEED_KMH, wind, heading_deg)
    return distance_km / speed


def should_return_to_base(
    battery: BatteryState,
    distance_to_base_km: float,
    payload_kg: float,
    wind: WindCondition,
    heading_to_base_deg: float,
) -> bool:
    from app.engine.routing import compute_battery_cost

    cost = compute_battery_cost(
        distance_to_base_km,
        payload_kg,
        battery.capacity_mah,
        wind.vector,
    )
    projected_pct = battery.current_pct - cost
    return projected_pct <= BATTERY_RETURN_THRESHOLD


def compute_heading(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    dlon = math.radians(lon2 - lon1)
    lat1r, lat2r = math.radians(lat1), math.radians(lat2)
    x = math.sin(dlon) * math.cos(lat2r)
    y = math.cos(lat1r) * math.sin(lat2r) - math.sin(lat1r) * math.cos(lat2r) * math.cos(dlon)
    return (math.degrees(math.atan2(x, y)) + 360) % 360
