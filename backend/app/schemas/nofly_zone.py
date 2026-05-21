from pydantic import BaseModel


class NoFlyZoneBase(BaseModel):
    name: str
    polygon_geojson: str


class NoFlyZoneCreate(NoFlyZoneBase):
    pass


class NoFlyZoneRead(NoFlyZoneBase):
    id: int

    model_config = {"from_attributes": True}
