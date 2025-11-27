
from typing import List
from pydantic import BaseModel
from .cubicle_dto import CubicleDto

class CubiclesListDto(BaseModel):
    toilet_id: int
    cubicles: List[CubicleDto]