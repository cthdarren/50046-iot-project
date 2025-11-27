from pydantic import BaseModel
from pydantic.config import ConfigDict

class CubicleDto(BaseModel):
    id: int
    toilet_id: int
    occupied: bool = False
    toilet_roll_percentage: int = 0
    

    model_config = ConfigDict(from_attributes=True)