from sqlalchemy import Column, Integer, String, Text
from app.database import Base


class NoFlyZone(Base):
    __tablename__ = "no_fly_zones"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    polygon_geojson = Column(Text, nullable=False)
