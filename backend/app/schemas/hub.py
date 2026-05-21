from pydantic import BaseModel


class HubBase(BaseModel):
    name: str
    latitude: float
    longitude: float
    is_charging_station: bool = True


class HubCreate(HubBase):
    pass


class HubRead(HubBase):
    id: int

    model_config = {"from_attributes": True}
