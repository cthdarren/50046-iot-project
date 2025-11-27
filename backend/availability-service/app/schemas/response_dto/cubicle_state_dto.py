from pydantic import BaseModel, ConfigDict
from datetime import datetime

class CubicleStateDto(BaseModel):
    id: int
    cubicle_id: int
    occupied: bool
    toilet_roll_percentage: int
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
