from shared.core.period import PeriodRange
from pydantic import BaseModel
from typing import List
from datetime import datetime


class CubicleEventDto(BaseModel):
    occupied: bool
    toilet_roll_percentage: int
    updated_at: datetime


class CubicleEventListDto(BaseModel):
    cubicle_id: int
    events: List[CubicleEventDto]


class ToiletEventDto(BaseModel):
    cubicles: List[CubicleEventListDto]


class FilterDto(BaseModel):
    period_range: PeriodRange


class FilteredCubicleEventDto(FilterDto):
    cubicle_id: int
    events: List[CubicleEventDto]


class FilteredToiletEventDto(FilterDto):
    toilet_id: int
    cubicles: List[CubicleEventListDto]


class FilteredMallEventDto(FilterDto):
    mall_id: int
    toilets: List[ToiletEventDto]
