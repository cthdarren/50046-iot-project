from pydantic import BaseModel
from datetime import datetime
from pydantic.config import ConfigDict

class CubicleEventDto(BaseModel):
    id: int
    cubicle_id: int
    timestamp: datetime
    occupied: bool
    toilet_roll_percentage: int

    model_config = ConfigDict(from_attributes=True)

class CubicleEventsListDto(BaseModel):
    cubicle_id: int
    events: list[CubicleEventDto]
