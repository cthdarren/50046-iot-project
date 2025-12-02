from pydantic import BaseModel
from shared.core.period import PeriodRange, Frequency
from datetime import datetime
from typing import Union, List


class MeanPercentageItem(BaseModel):
    mean_percentage: float


class HourlyMeanPercentageItem(MeanPercentageItem):
    hour: datetime


class DailyMeanPercentageItem(MeanPercentageItem):
    day: datetime


class MeanPercentageDto(BaseModel):
    frequency: Frequency
    period_range: PeriodRange
    mean_percentages: Union[
        List[HourlyMeanPercentageItem], List[DailyMeanPercentageItem]
    ]
    highest_mean_datetime: datetime | None
    lowest_mean_datetime: datetime | None
