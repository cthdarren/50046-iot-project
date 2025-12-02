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
from core.config import settings
from core.schemas.mean_dto import (
    HourlyMeanPercentageItem,
    DailyMeanPercentageItem,
)
from shared.core.exceptions import handle_api_exception
from pydantic import TypeAdapter


class AnalyticsService:

    async def get_events(
        self,
        mall_id: int,
        toilet_id: Optional[int] = None,
        cubicle_id: Optional[int] = None,
        period_range: PeriodRange = PeriodRange(
            start_date=datetime.now(), end_date=datetime.now()
        ),
    ) -> Tuple[
        Union[FilteredMallEventDto, FilteredToiletEventDto, FilteredCubicleEventDto],
        AggregationLevel,
    ]:
        # call api from availability-service's /events endpoint
        toilet_param = f"&toilet_id={toilet_id}" if toilet_id else ""
        cubicle_param = f"&cubicle_id={cubicle_id}" if cubicle_id else ""
        try:
            response = requests.get(
                f"{settings.AVAILABILITY_SERVICE_URL}:{settings.AVAILABILITY_SERVICE_PORT}/events?mall_id={mall_id}{toilet_param}{cubicle_param}&start_date={period_range.start_date}&end_date={period_range.end_date}"
            )
        except requests.exceptions.RequestException as e:
            raise ApiException(ErrorCodes.INTERNAL_SERVER_ERROR, str(e))

        if response.status_code != 200:
            await handle_api_exception(int(response.status_code))

        if toilet_id:
            if cubicle_id:
                cubicle_event: FilteredCubicleEventDto = TypeAdapter(
                    FilteredCubicleEventDto
                ).validate_python(response.json())
                return cubicle_event, AggregationLevel.cubicle
            else:
                toilet_event: FilteredToiletEventDto = TypeAdapter(
                    FilteredToiletEventDto
                ).validate_python(response.json())
                return toilet_event, AggregationLevel.toilet

        mall_event: FilteredMallEventDto = TypeAdapter(
            FilteredMallEventDto
        ).validate_python(response.json())
        return mall_event, AggregationLevel.mall

    async def aggregate_events(
        self,
        event_data: Union[
            FilteredMallEventDto, FilteredToiletEventDto, FilteredCubicleEventDto
        ],
        aggregation_level: AggregationLevel,
        frequency: Frequency,
    ) -> Union[
        Tuple[List[HourlyAggregationItem], datetime | None, datetime | None],
        Tuple[List[DailyAggregationItem], datetime | None, datetime | None],
    ]:
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
    ) -> Tuple[List[HourlyAggregationItem], datetime | None, datetime | None]:
        timestamp_count = defaultdict(int)
        peak_hour, peak_count = None, 0
        lowest_hour, lowest_count = None, float("inf")
        for toilet in filtered_mall_events.toilets:
            for cubicle in toilet.cubicles:
                for event in cubicle.events:
                    if event.occupied:
                        timestamp: datetime = await self.truncate_timestamp(
                            event.updated_at, Frequency.hour
                        )
                        timestamp_count[timestamp] += 1
                        if timestamp_count[timestamp] > peak_count:
                            peak_hour = timestamp
                            peak_count = timestamp_count[timestamp]
                        if timestamp_count[timestamp] < lowest_count:
                            lowest_hour = timestamp
                            lowest_count = timestamp_count[timestamp]
        return (
            [
                HourlyAggregationItem(hour=k, occupied_count=v)
                for k, v in sorted(timestamp_count.items())
            ],
            peak_hour,
            lowest_hour,
        )

    async def aggregate_toilet_hourly(
        self, filtered_toilet_events: FilteredToiletEventDto
    ) -> Tuple[List[HourlyAggregationItem], datetime | None, datetime | None]:
        timestamp_count = defaultdict(int)
        peak_hour, peak_count = None, 0
        lowest_hour, lowest_count = None, float("inf")
        for cubicle in filtered_toilet_events.cubicles:
            for event in cubicle.events:
                if event.occupied:
                    timestamp: datetime = await self.truncate_timestamp(
                        event.updated_at, Frequency.hour
                    )
                    timestamp_count[timestamp] += 1
                    if timestamp_count[timestamp] > peak_count:
                        peak_hour = timestamp
                        peak_count = timestamp_count[timestamp]
                    if timestamp_count[timestamp] < lowest_count:
                        lowest_hour = timestamp
                        lowest_count = timestamp_count[timestamp]
        return (
            [
                HourlyAggregationItem(hour=k, occupied_count=v)
                for k, v in sorted(timestamp_count.items())
            ],
            peak_hour,
            lowest_hour,
        )

    async def aggregate_cubicle_hourly(
        self, filtered_cubicle_events: FilteredCubicleEventDto
    ) -> Tuple[List[HourlyAggregationItem], datetime | None, datetime | None]:
        timestamp_count = defaultdict(int)
        peak_hour, peak_count = None, 0
        lowest_hour, lowest_count = None, float("inf")
        for event in filtered_cubicle_events.events:
            if event.occupied:
                timestamp: datetime = await self.truncate_timestamp(
                    event.updated_at, Frequency.hour
                )
                timestamp_count[timestamp] += 1
                if timestamp_count[timestamp] > peak_count:
                    peak_hour = timestamp
                    peak_count = timestamp_count[timestamp]
                if timestamp_count[timestamp] < lowest_count:
                    lowest_hour = timestamp
                    lowest_count = timestamp_count[timestamp]
        return (
            [
                HourlyAggregationItem(hour=k, occupied_count=v)
                for k, v in sorted(timestamp_count.items())
            ],
            peak_hour,
            lowest_hour,
        )

    async def aggregate_mall_daily(
        self, filtered_mall_events: FilteredMallEventDto
    ) -> Tuple[List[DailyAggregationItem], datetime | None, datetime | None]:
        timestamp_count = defaultdict(int)
        peak_day, peak_count = None, 0
        lowest_day, lowest_count = None, float("inf")
        for toilet in filtered_mall_events.toilets:
            for cubicle in toilet.cubicles:
                for event in cubicle.events:
                    if event.occupied:
                        timestamp: datetime = await self.truncate_timestamp(
                            event.updated_at, Frequency.day
                        )
                        timestamp_count[timestamp] += 1
                        if timestamp_count[timestamp] > peak_count:
                            peak_day = timestamp
                            peak_count = timestamp_count[timestamp]
                        if timestamp_count[timestamp] < lowest_count:
                            lowest_day = timestamp
                            lowest_count = timestamp_count[timestamp]

        return (
            [
                DailyAggregationItem(day=k, occupied_count=v)
                for k, v in sorted(timestamp_count.items())
            ],
            peak_day,
            lowest_day,
        )

    async def aggregate_toilet_daily(
        self, filtered_toilet_events: FilteredToiletEventDto
    ) -> Tuple[List[DailyAggregationItem], datetime | None, datetime | None]:
        timestamp_count = defaultdict(int)
        peak_day, peak_count = None, 0
        lowest_day, lowest_count = None, float("inf")
        for cubicle in filtered_toilet_events.cubicles:
            for event in cubicle.events:
                if event.occupied:
                    timestamp: datetime = await self.truncate_timestamp(
                        event.updated_at, Frequency.day
                    )
                    timestamp_count[timestamp] += 1
                    if timestamp_count[timestamp] > peak_count:
                        peak_day = timestamp
                        peak_count = timestamp_count[timestamp]
                    if timestamp_count[timestamp] < lowest_count:
                        lowest_day = timestamp
                        lowest_count = timestamp_count[timestamp]
        return (
            [
                DailyAggregationItem(day=k, occupied_count=v)
                for k, v in sorted(timestamp_count.items())
            ],
            peak_day,
            lowest_day,
        )

    async def aggregate_cubicle_daily(
        self, filtered_cubicle_events: FilteredCubicleEventDto
    ) -> Tuple[List[DailyAggregationItem], datetime | None, datetime | None]:
        timestamp_count = defaultdict(int)
        peak_day, peak_count = None, 0
        lowest_day, lowest_count = None, float("inf")
        for event in filtered_cubicle_events.events:
            if event.occupied:
                timestamp: datetime = await self.truncate_timestamp(
                    event.updated_at, Frequency.day
                )
                timestamp_count[timestamp] += 1
                if timestamp_count[timestamp] > peak_count:
                    peak_day = timestamp
                    peak_count = timestamp_count[timestamp]
                if timestamp_count[timestamp] < lowest_count:
                    lowest_day = timestamp
                    lowest_count = timestamp_count[timestamp]
        return (
            [
                DailyAggregationItem(day=k, occupied_count=v)
                for k, v in sorted(timestamp_count.items())
            ],
            peak_day,
            lowest_day,
        )

    async def calculate_mean_toilet_roll_consumption(
        self,
        event_data: Union[
            FilteredMallEventDto, FilteredToiletEventDto, FilteredCubicleEventDto
        ],
        aggregation_level: AggregationLevel,
        frequency: Frequency,
    ):
        if aggregation_level == AggregationLevel.toilet and isinstance(
            event_data, FilteredToiletEventDto
        ):
            return await self.mean_toilet_toilet_roll_consumption(event_data, frequency)
        elif aggregation_level == AggregationLevel.cubicle and isinstance(
            event_data, FilteredCubicleEventDto
        ):
            return await self.mean_cubicle_toilet_roll_consumption(
                event_data, frequency
            )
        elif aggregation_level == AggregationLevel.mall and isinstance(
            event_data, FilteredMallEventDto
        ):
            return await self.mean_mall_toilet_roll_consumption(event_data, frequency)
        else:
            raise ValueError("Invalid aggregation level")

    async def mean_cubicle_toilet_roll_consumption(
        self, filtered_cubicle_events: FilteredCubicleEventDto, frequency: Frequency
    ) -> Tuple[
        Union[List[HourlyMeanPercentageItem], List[DailyMeanPercentageItem]],
        datetime | None,
        datetime | None,
    ]:
        timestamp_percentage_sum = defaultdict(int)
        timestamp_count = defaultdict(int)

        for event in filtered_cubicle_events.events:
            timestamp: datetime = await self.truncate_timestamp(
                event.updated_at, frequency
            )
            toilet_roll_percentage = event.toilet_roll_percentage
            if toilet_roll_percentage > 100:
                toilet_roll_percentage = 100
            if toilet_roll_percentage < 0:
                toilet_roll_percentage = 0
            timestamp_percentage_sum[timestamp] += toilet_roll_percentage
            timestamp_count[timestamp] += 1

        if frequency == Frequency.hour:
            hourly_result: List[HourlyMeanPercentageItem] = [
                HourlyMeanPercentageItem(hour=k, mean_percentage=v / timestamp_count[k])
                for k, v in sorted(timestamp_percentage_sum.items())
            ]
            highest_mean_datetime = None
            lowest_mean_datetime = None
            if hourly_result:
                highest_mean_datetime = max(
                    hourly_result, key=lambda x: x.mean_percentage
                ).hour
                lowest_mean_datetime = min(
                    hourly_result, key=lambda x: x.mean_percentage
                ).hour
            return hourly_result, highest_mean_datetime, lowest_mean_datetime
        else:
            daily_result: List[DailyMeanPercentageItem] = [
                DailyMeanPercentageItem(day=k, mean_percentage=v / timestamp_count[k])
                for k, v in sorted(timestamp_percentage_sum.items())
            ]
            highest_mean_datetime = None
            lowest_mean_datetime = None
            if daily_result:
                highest_mean_datetime = max(
                    daily_result, key=lambda x: x.mean_percentage
                ).day
                lowest_mean_datetime = min(
                    daily_result, key=lambda x: x.mean_percentage
                ).day
            return daily_result, highest_mean_datetime, lowest_mean_datetime

    async def mean_toilet_toilet_roll_consumption(
        self, filtered_toilet_events: FilteredToiletEventDto, frequency: Frequency
    ) -> Tuple[
        Union[List[HourlyMeanPercentageItem], List[DailyMeanPercentageItem]],
        datetime | None,
        datetime | None,
    ]:
        timestamp_percentage_sum = defaultdict(int)
        timestamp_count = defaultdict(int)

        for cubicle in filtered_toilet_events.cubicles:
            for event in cubicle.events:
                timestamp: datetime = await self.truncate_timestamp(
                    event.updated_at, frequency
                )
                toilet_roll_percentage = event.toilet_roll_percentage
                if toilet_roll_percentage > 100:
                    toilet_roll_percentage = 100
                if toilet_roll_percentage < 0:
                    toilet_roll_percentage = 0
                timestamp_percentage_sum[timestamp] += toilet_roll_percentage
                timestamp_count[timestamp] += 1

        if frequency == Frequency.hour:
            hourly_result: List[HourlyMeanPercentageItem] = [
                HourlyMeanPercentageItem(hour=k, mean_percentage=v / timestamp_count[k])
                for k, v in sorted(timestamp_percentage_sum.items())
            ]
            highest_mean_datetime = None
            lowest_mean_datetime = None
            if hourly_result:
                highest_mean_datetime = max(
                    hourly_result, key=lambda x: x.mean_percentage
                ).hour
                lowest_mean_datetime = min(
                    hourly_result, key=lambda x: x.mean_percentage
                ).hour
            return hourly_result, highest_mean_datetime, lowest_mean_datetime
        else:
            daily_result: List[DailyMeanPercentageItem] = [
                DailyMeanPercentageItem(day=k, mean_percentage=v / timestamp_count[k])
                for k, v in sorted(timestamp_percentage_sum.items())
            ]
            highest_mean_datetime = None
            lowest_mean_datetime = None
            if daily_result:
                highest_mean_datetime = max(
                    daily_result, key=lambda x: x.mean_percentage
                ).day
                lowest_mean_datetime = min(
                    daily_result, key=lambda x: x.mean_percentage
                ).day
            return daily_result, highest_mean_datetime, lowest_mean_datetime

    async def mean_mall_toilet_roll_consumption(
        self, filtered_mall_events: FilteredMallEventDto, frequency: Frequency
    ) -> Tuple[
        Union[List[HourlyMeanPercentageItem], List[DailyMeanPercentageItem]],
        datetime | None,
        datetime | None,
    ]:
        timestamp_percentage_sum = defaultdict(int)
        timestamp_count = defaultdict(int)

        for toilet in filtered_mall_events.toilets:
            for cubicle in toilet.cubicles:
                for event in cubicle.events:
                    timestamp: datetime = await self.truncate_timestamp(
                        event.updated_at, frequency
                    )
                    toilet_roll_percentage = event.toilet_roll_percentage
                    # if toilet_roll_percentage > 100:
                    #     toilet_roll_percentage = 100
                    # if toilet_roll_percentage < 0:
                    #     toilet_roll_percentage = 0
                    timestamp_percentage_sum[timestamp] += toilet_roll_percentage
                    timestamp_count[timestamp] += 1

        if frequency == Frequency.hour:
            hourly_result: List[HourlyMeanPercentageItem] = [
                HourlyMeanPercentageItem(hour=k, mean_percentage=v / timestamp_count[k])
                for k, v in sorted(timestamp_percentage_sum.items())
            ]
            highest_mean_datetime = None
            lowest_mean_datetime = None
            if hourly_result:
                highest_mean_datetime = max(
                    hourly_result, key=lambda x: x.mean_percentage
                ).hour
                lowest_mean_datetime = min(
                    hourly_result, key=lambda x: x.mean_percentage
                ).hour
            return hourly_result, highest_mean_datetime, lowest_mean_datetime
        else:
            daily_result: List[DailyMeanPercentageItem] = [
                DailyMeanPercentageItem(day=k, mean_percentage=v / timestamp_count[k])
                for k, v in sorted(timestamp_percentage_sum.items())
            ]
            highest_mean_datetime = None
            lowest_mean_datetime = None
            if daily_result:
                highest_mean_datetime = max(
                    daily_result, key=lambda x: x.mean_percentage
                ).day
                lowest_mean_datetime = min(
                    daily_result, key=lambda x: x.mean_percentage
                ).day
            return daily_result, highest_mean_datetime, lowest_mean_datetime
