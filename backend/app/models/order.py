from sqlalchemy import Column, Integer, String, Float, Enum as SAEnum
from app.database import Base
import enum


class OrderStatus(str, enum.Enum):
    pending = "pending"
    assigned = "assigned"
    in_transit = "in_transit"
    delivered = "delivered"
    cancelled = "cancelled"


class PriorityLevel(str, enum.Enum):
    low = "low"
    medium = "medium"
    high = "high"
    critical = "critical"


class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    pickup_lat = Column(Float, nullable=False)
    pickup_lon = Column(Float, nullable=False)
    dropoff_lat = Column(Float, nullable=False)
    dropoff_lon = Column(Float, nullable=False)
    package_weight_kg = Column(Float, nullable=False)
    priority = Column(
        SAEnum("low", "medium", "high", "critical", name="priority_level", create_constraint=True),
        default=PriorityLevel.medium.value,
        nullable=False,
    )
    status = Column(
        SAEnum("pending", "assigned", "in_transit", "delivered", "cancelled", name="order_status", create_constraint=True),
        default=OrderStatus.pending.value,
        nullable=False,
    )
    assigned_drone_id = Column(Integer, nullable=True)
