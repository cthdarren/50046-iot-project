from pydantic import BaseModel, ConfigDict
from datetime import datetime

class CubicleEventDto(BaseModel):
    id: int
    cubicle_id: int
    toilet_roll_percentage: int
    timestamp: datetime

    model_config = ConfigDict(from_attributes=True)