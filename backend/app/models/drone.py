from sqlalchemy import Column, Integer, String, Float, Enum as SAEnum
from app.database import Base
import enum


class DroneStatus(str, enum.Enum):
    idle = "idle"
    charging = "charging"
    en_route = "en_route"


class Drone(Base):
    __tablename__ = "drones"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    status = Column(SAEnum(DroneStatus), default=DroneStatus.idle, nullable=False)
    max_payload_kg = Column(Float, nullable=False)
    battery_capacity_mah = Column(Integer, nullable=False)
    battery_pct = Column(Float, default=100.0, nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    home_hub_id = Column(Integer, nullable=True)
