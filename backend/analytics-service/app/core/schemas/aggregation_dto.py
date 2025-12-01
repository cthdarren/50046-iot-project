from pydantic import BaseModel
from shared.core.period import Frequency, PeriodRange
from core.enum import AggregationLevel
from typing import List, Union
from datetime import datetime

class AggregationItem(BaseModel):
    occupied_count: int

class HourlyAggregationItem(AggregationItem):
    hour: datetime

class DailyAggregationItem(AggregationItem):
    day: datetime

class AggregationDto(BaseModel):
    frequency: Frequency
    period_range: PeriodRange
    aggregation_level: AggregationLevel
    aggregation: Union[List[HourlyAggregationItem], List[DailyAggregationItem]]
    peak: datetime | None = None
    lowest: datetime | None = None