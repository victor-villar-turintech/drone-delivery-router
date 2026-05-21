from pydantic import BaseModel
from app.models.drone import DroneStatus


class DroneBase(BaseModel):
    name: str
    max_payload_kg: float
    battery_capacity_mah: int
    battery_pct: float = 100.0
    latitude: float
    longitude: float
    home_hub_id: int | None = None


class DroneCreate(DroneBase):
    pass


class DroneRead(DroneBase):
    id: int
    status: DroneStatus

    model_config = {"from_attributes": True}


class DroneUpdate(BaseModel):
    status: DroneStatus | None = None
    battery_pct: float | None = None
    latitude: float | None = None
    longitude: float | None = None
