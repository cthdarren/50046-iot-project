from shared.schemas.state import (
    FilteredMallEventDto,
    FilteredToiletEventDto,
    FilteredCubicleEventDto,
)
from shared.core.period import PeriodRange, Frequency
from typing import Optional, Union, List, Tuple
from datetime import datetime
from shared.core.exceptions import ApiException, ErrorCodes
from core.enum import AggregationLevel
from core.schemas.aggregation_dto import HourlyAggregationItem, DailyAggregationItem
from collections import defaultdict
import requests


class AnalyticsService:

    async def get_events(
        self,
        mall_id: int,
        toilet_id: Optional[int] = None,
        cubicle_id: Optional[int] = None,
        period_range: PeriodRange = PeriodRange(
            start_date=datetime.now(), end_date=datetime.now()
        ),
    ) -> Tuple[Union[FilteredMallEventDto, FilteredToiletEventDto, FilteredCubicleEventDto], AggregationLevel]:
        # call api from availability-service's /events endpoint
        toilet_param = f"&toilet_id={toilet_id}" if toilet_id else ""
        cubicle_param = f"&cubicle_id={cubicle_id}" if cubicle_id else ""
        response = requests.get(
            f"http://availability-service:8001/events?mall_id={mall_id}{toilet_param}{cubicle_param}&start_date={period_range.start_date}&end_date={period_range.end_date}"
        )
        if response.status_code != 200:
            raise ApiException(ErrorCodes.INTERNAL_SERVER_ERROR, "Failed to get events")
        
        if cubicle_id:
            return FilteredCubicleEventDto(**response.json()), AggregationLevel.cubicle
        elif toilet_id:
            return FilteredToiletEventDto(**response.json()), AggregationLevel.toilet

        return FilteredMallEventDto(**response.json()), AggregationLevel.mall
        

    async def aggregate_events(
        self,
        event_data: Union[
            FilteredMallEventDto, FilteredToiletEventDto, FilteredCubicleEventDto
        ],
        aggregation_level: AggregationLevel,
        frequency: Frequency,
    ) -> Union[List[HourlyAggregationItem], List[DailyAggregationItem]]:
        if frequency == Frequency.day:
            if aggregation_level == AggregationLevel.mall and isinstance(
                event_data, FilteredMallEventDto
            ):
                return await self.aggregate_mall_daily(event_data)
            elif aggregation_level == AggregationLevel.toilet and isinstance(
                event_data, FilteredToiletEventDto
            ):
                return await self.aggregate_toilet_daily(event_data)
            elif aggregation_level == AggregationLevel.cubicle and isinstance(
                event_data, FilteredCubicleEventDto
            ):
                return await self.aggregate_cubicle_daily(event_data)
        elif frequency == Frequency.hour:
            if aggregation_level == AggregationLevel.mall and isinstance(
                event_data, FilteredMallEventDto
            ):
                return await self.aggregate_mall_hourly(event_data)
            elif aggregation_level == AggregationLevel.toilet and isinstance(
                event_data, FilteredToiletEventDto
            ):
                return await self.aggregate_toilet_hourly(event_data)
            elif aggregation_level == AggregationLevel.cubicle and isinstance(
                event_data, FilteredCubicleEventDto
            ):
                return await self.aggregate_cubicle_hourly(event_data)
        raise ApiException(
            ErrorCodes.INTERNAL_SERVER_ERROR, "Failed to aggregate events"
        )

    async def truncate_timestamp(
        self, timestamp: datetime, frequency: Frequency
    ) -> datetime:
        if frequency == Frequency.hour:
            return timestamp.replace(minute=0, second=0, microsecond=0)
        elif frequency == Frequency.day:
            return timestamp.replace(hour=0, minute=0, second=0, microsecond=0)

    async def aggregate_mall_hourly(
        self, filtered_mall_events: FilteredMallEventDto
    ) -> List[HourlyAggregationItem]:
        timestamp_count = defaultdict(int)
        for toilet in filtered_mall_events.toilets:
            for cubicle in toilet.cubicles:
                for event in cubicle.events:
                    if event.occupied:
                        timestamp_count[
                            await self.truncate_timestamp(event.updated_at, Frequency.hour)
                        ] += 1
        return [
            HourlyAggregationItem(hour=k, occupied_count=v)
            for k, v in sorted(timestamp_count.items())
        ]

    async def aggregate_toilet_hourly(
        self, filtered_toilet_events: FilteredToiletEventDto
    ) -> List[HourlyAggregationItem]:
        timestamp_count = defaultdict(int)
        for cubicle in filtered_toilet_events.cubicles:
            for event in cubicle.events:
                if event.occupied:
                    timestamp_count[
                        await self.truncate_timestamp(event.updated_at, Frequency.hour)
                    ] += 1
        return [
            HourlyAggregationItem(hour=k, occupied_count=v)
            for k, v in sorted(timestamp_count.items())
        ]

    async def aggregate_cubicle_hourly(
        self, filtered_cubicle_events: FilteredCubicleEventDto
    ) -> List[HourlyAggregationItem]:
        timestamp_count = defaultdict(int)
        for event in filtered_cubicle_events.events:
            if event.occupied:
                timestamp_count[
                    await self.truncate_timestamp(event.updated_at, Frequency.hour)
                ] += 1
        return [
            HourlyAggregationItem(hour=k, occupied_count=v)
            for k, v in sorted(timestamp_count.items())
        ]

    async def aggregate_mall_daily(
        self, filtered_mall_events: FilteredMallEventDto
    ) -> List[DailyAggregationItem]:
        timestamp_count = defaultdict(int)
        for toilet in filtered_mall_events.toilets:
            for cubicle in toilet.cubicles:
                for event in cubicle.events:
                    if event.occupied:
                        timestamp_count[
                            await self.truncate_timestamp(event.updated_at, Frequency.day)
                        ] += 1
        return [
            DailyAggregationItem(day=k, occupied_count=v)
            for k, v in sorted(timestamp_count.items())
        ]

    async def aggregate_toilet_daily(
        self, filtered_toilet_events: FilteredToiletEventDto
    ) -> List[DailyAggregationItem]:
        timestamp_count = defaultdict(int)
        for cubicle in filtered_toilet_events.cubicles:
            for event in cubicle.events:
                if event.occupied:
                    timestamp_count[
                        await self.truncate_timestamp(event.updated_at, Frequency.day)
                    ] += 1
        return [
            DailyAggregationItem(day=k, occupied_count=v)
            for k, v in sorted(timestamp_count.items())
        ]

    async def aggregate_cubicle_daily(
        self, filtered_cubicle_events: FilteredCubicleEventDto
    ) -> List[DailyAggregationItem]:
        timestamp_count = defaultdict(int)
        for event in filtered_cubicle_events.events:
            if event.occupied:
                timestamp_count[
                    await self.truncate_timestamp(event.updated_at, Frequency.day)
                ] += 1
        return [
            DailyAggregationItem(day=k, occupied_count=v)
            for k, v in sorted(timestamp_count.items())
        ]
