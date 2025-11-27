
from pydantic import BaseModel
from .cubicle_dto import CubicleDto
from typing import Sequence

class CubiclesListDto(BaseModel):
    toilet_id: int
    cubicles: Sequence[CubicleDto]