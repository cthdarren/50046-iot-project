from fastapi import APIRouter, Depends
from shared.core.period import Frequency, PeriodRange
from datetime import datetime
from typing import Optional, Union
from ..services.analytics_service import AnalyticsService
from core.schemas.aggregation_dto import HourlyAggregationItem, DailyAggregationItem
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
) -> Union[List[HourlyAggregationItem], List[DailyAggregationItem]]:
    event_data, aggregation_level = await analytics_service.get_events(
        mall_id=mall_id,
        toilet_id=toilet_id,
        cubicle_id=cubicle_id,
        period_range=PeriodRange(start_date=start_date, end_date=end_date),
    )
    aggregation: Union[List[HourlyAggregationItem], List[DailyAggregationItem]] = (
        await analytics_service.aggregate_events(
            event_data=event_data,
            aggregation_level=aggregation_level,
            frequency=frequency,
        )
    )
    return aggregation
