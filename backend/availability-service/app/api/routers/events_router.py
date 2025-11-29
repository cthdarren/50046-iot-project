from fastapi import APIRouter, Response
from shared.core.period import Period, PeriodRange
from api.services.events_service import EventsService
from fastapi import Depends
from typing import Sequence, Optional, Union
from db.models import CubicleState
from shared.schemas.latest_state import (
    LatestCubicleStateDto,
    LatestToiletStateDto,
    LatestMallStateDto,
)


router = APIRouter(prefix="/events")


@router.get("/")
async def get_events(
    period_range: PeriodRange | None = None,
    period: Period | None = None,
    mall_id: int | None = None,
    toilet_id: int | None = None,
    cubicle_id: int | None = None,
    events_service: EventsService = Depends(),
):
    return Response(content={"message": "Not implemented"})
    # return await events_service.get_events(period_range, period, mall_id, toilet_id, cubicle_id)


@router.get("/latest")
async def get_latest_state(
    mall_id: int,
    toilet_id: Optional[int] = None,
    cubicle_id: Optional[int] = None,
    events_service: EventsService = Depends(),
):
    if toilet_id:
        if cubicle_id:
            return await events_service.get_latest_cubicle_state(
                mall_id, toilet_id, cubicle_id
            )
        return await events_service.get_latest_toilet_state(mall_id, toilet_id)
    return await events_service.get_latest_mall_state(mall_id)
