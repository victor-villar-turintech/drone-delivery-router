from pydantic import BaseModel
from app.models.order import OrderStatus, PriorityLevel


class OrderBase(BaseModel):
    pickup_lat: float
    pickup_lon: float
    dropoff_lat: float
    dropoff_lon: float
    package_weight_kg: float
    priority: PriorityLevel = PriorityLevel.medium


class OrderCreate(OrderBase):
    pass


class OrderRead(OrderBase):
    id: int
    status: OrderStatus
    assigned_drone_id: int | None = None

    model_config = {"from_attributes": True}
