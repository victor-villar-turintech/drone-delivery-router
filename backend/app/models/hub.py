from sqlalchemy import Column, Integer, String, Float, Boolean
from app.database import Base


class Hub(Base):
    __tablename__ = "hubs"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    is_charging_station = Column(Boolean, default=True, nullable=False)
