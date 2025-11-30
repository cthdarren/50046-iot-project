from fastapi import APIRouter, Depends
from shared.core.period import Frequency, PeriodRange
from datetime import datetime
from typing import Optional, Union, Tuple
from ..services.analytics_service import AnalyticsService
from core.schemas.aggregation_dto import (
    HourlyAggregationItem,
    DailyAggregationItem,
    AggregationDto,
)
from core.schemas.mean_dto import (
    HourlyMeanPercentageItem,
    DailyMeanPercentageItem,
    MeanPercentageDto,
)
from typing import List

router = APIRouter(prefix="/analytics")


@router.get("/")
async def read_root():
    return {"Analytics service is running."}


@router.get("/aggregation")
async def get_mall_analytics(
    mall_id: int,
    toilet_id: Optional[int] = None,
    cubicle_id: Optional[int] = None,
    frequency: Frequency = Frequency.hour,
    start_date: datetime = datetime.now(),
    end_date: datetime = datetime.now(),
    analytics_service: AnalyticsService = Depends(),
) -> AggregationDto:
    event_data, aggregation_level = await analytics_service.get_events(
        mall_id=mall_id,
        toilet_id=toilet_id,
        cubicle_id=cubicle_id,
        period_range=PeriodRange(start_date=start_date, end_date=end_date),
    )
    aggregation_data: Union[
        Tuple[List[HourlyAggregationItem], datetime | None, datetime | None],
        Tuple[List[DailyAggregationItem], datetime | None, datetime | None],
    ] = await analytics_service.aggregate_events(
        event_data=event_data,
        aggregation_level=aggregation_level,
        frequency=frequency,
    )
    aggregation, peak, lowest = aggregation_data
    return AggregationDto(
        frequency=frequency,
        period_range=PeriodRange(start_date=start_date, end_date=end_date),
        aggregation_level=aggregation_level,
        aggregation=aggregation,
        peak=peak,
        lowest=lowest,
    )


@router.get("/toilet-roll-mean")
async def get_toilet_roll_mean(
    mall_id: int,
    toilet_id: Optional[int] = None,
    cubicle_id: Optional[int] = None,
    frequency: Frequency = Frequency.hour,
    start_date: datetime = datetime.now(),
    end_date: datetime = datetime.now(),
    analytics_service: AnalyticsService = Depends(),
) -> MeanPercentageDto:
    event_data, aggregation_level = await analytics_service.get_events(
        mall_id=mall_id,
        toilet_id=toilet_id,
        cubicle_id=cubicle_id,
        period_range=PeriodRange(start_date=start_date, end_date=end_date),
    )
    mean_data: Tuple[
        Union[List[HourlyMeanPercentageItem], List[DailyMeanPercentageItem]],
        datetime | None,
        datetime | None,
    ] = await analytics_service.calculate_mean_toilet_roll_consumption(
        event_data=event_data,
        frequency=frequency,
        aggregation_level=aggregation_level,
    )
    mean_percentage, peak, lowest = mean_data
    return MeanPercentageDto(
        frequency=frequency,
        period_range=PeriodRange(start_date=start_date, end_date=end_date),
        mean_percentages=mean_percentage,
        highest_mean_datetime=peak,
        lowest_mean_datetime=lowest,
    )
