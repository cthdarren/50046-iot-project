from pydantic import BaseModel
from datetime import datetime
from typing import List, Sequence

class LatestCubicleStateDto(BaseModel):
    cubicle_id: int
    occupied: bool
    toilet_roll_percentage: int
    updated_at: datetime

class LatestToiletStateDto(BaseModel):
    toilet_id: int
    cubicles: List[LatestCubicleStateDto]

class LatestMallStateDto(BaseModel):
    mall_id: int
    toilets: List[LatestToiletStateDto]