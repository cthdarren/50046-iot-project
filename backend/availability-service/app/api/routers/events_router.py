from datetime import datetime
from fastapi import APIRouter, Response
from shared.core.period import PeriodRange
from api.services.events_service import EventsService
from fastapi import Depends
from typing import Optional, Union
from shared.schemas.state import (
    FilteredCubicleEventDto,
    FilteredToiletEventDto,
    FilteredMallEventDto,
)
from shared.schemas.latest_state import (
    LatestCubicleStateDto,
    LatestToiletStateDto,
    LatestMallStateDto,
)


router = APIRouter(prefix="/events")


@router.get(
    "/",
    response_model=Union[
        FilteredCubicleEventDto, FilteredToiletEventDto, FilteredMallEventDto
    ],
)
async def get_events(
    mall_id: int,
    toilet_id: Optional[int] = None,
    cubicle_id: Optional[int] = None,
    start_date=datetime.now(),
    end_date=datetime.now(),
    events_service: EventsService = Depends(),
):
    return await events_service.get_events(
        mall_id=mall_id,
        toilet_id=toilet_id,
        cubicle_id=cubicle_id,
        period_range=PeriodRange(start_date=start_date, end_date=end_date),
    )


@router.get(
    "/latest",
    response_model=Union[
        LatestCubicleStateDto, LatestToiletStateDto, LatestMallStateDto
    ],
)
async def get_latest_state(
    mall_id: int,
    toilet_id: Optional[int] = None,
    cubicle_id: Optional[int] = None,
    events_service: EventsService = Depends(),
) -> Union[LatestCubicleStateDto, LatestToiletStateDto, LatestMallStateDto]:
    if toilet_id:
        if cubicle_id:
            return await events_service.get_latest_cubicle_state(
                mall_id, toilet_id, cubicle_id
            )
        return await events_service.get_latest_toilet_state(mall_id, toilet_id)
    return await events_service.get_latest_mall_state(mall_id)
