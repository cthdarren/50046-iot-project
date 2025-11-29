from pydantic import BaseModel
from shared.core.period import Frequency, PeriodRange
from core.enum import AggregationLevel
from typing import List, Union
from datetime import datetime

class HourlyAggregationItem(BaseModel):
    hour: datetime
    occupied_count: int

class DailyAggregationItem(BaseModel):
    day: datetime
    occupied_count: int

class AggregationDto(BaseModel):
    frequency: Frequency
    period_range: PeriodRange
    aggregation_level: AggregationLevel
    aggregation: List[Union[HourlyAggregationItem, DailyAggregationItem]]