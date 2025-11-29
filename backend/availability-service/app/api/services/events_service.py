from db.database import get_db
from ..repo.events_repo import EventsRepo
from shared.core.period import PeriodRange, Period
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends
from typing import Sequence
from db.models import CubicleState, Toilet
from api.services.toilets_service import ToiletsService
from api.services.cubicles_service import CubiclesService
from core.exceptions import NotFoundException
from shared.schemas.latest_state import (
    LatestCubicleStateDto,
    LatestToiletStateDto,
    LatestMallStateDto,
)


class EventsService:
    def __init__(
        self,
        db: AsyncSession = Depends(get_db),
        toilets_service: ToiletsService = Depends(),
        cubicles_service: CubiclesService = Depends(),
    ) -> None:
        self.events_repo = EventsRepo(db)
        self.toilets_service = toilets_service
        self.cubicles_service = cubicles_service

    async def get_events(
        self,
        period_range: PeriodRange | None = None,
        period: Period | None = None,
        mall_id: int | None = None,
        toilet_id: int | None = None,
        cubicle_id: int | None = None,
    ):
        return await self.events_repo.get_events(
            period_range, period, mall_id, toilet_id, cubicle_id
        )

    async def get_latest_cubicle_state(
        self, mall_id: int, toilet_id: int, cubicle_id: int
    ):
        if not await self.cubicles_service.get_cubicle(
            mall_id=mall_id, toilet_id=toilet_id, cubicle_id=cubicle_id
        ):
            raise NotFoundException(detail="Cubicle not found.")
        cubicle_state: CubicleState = await self.events_repo.get_latest_cubicle_state(
            cubicle_id
        )
        if not cubicle_state:
            raise NotFoundException(detail="Cubicle state not found.")
        return LatestCubicleStateDto(
            cubicle_id=cubicle_state.__getattribute__("cubicle_id"),
            occupied=cubicle_state.__getattribute__("occupied"),
            toilet_roll_percentage=cubicle_state.__getattribute__(
                "toilet_roll_percentage"
            ),
            updated_at=cubicle_state.__getattribute__("updated_at"),
        )

    async def get_latest_toilet_state(
        self, mall_id: int, toilet_id: int
    ) -> LatestToiletStateDto:
        if not await self.toilets_service.get_toilet(
            mall_id=mall_id, toilet_id=toilet_id
        ):
            raise NotFoundException(detail="Toilet not found.")
        cubicle_states: Sequence[CubicleState] = (
            await self.events_repo.get_latest_toilet_state(toilet_id)
        )
        return LatestToiletStateDto(
            toilet_id=toilet_id,
            cubicles=[
                LatestCubicleStateDto(
                    cubicle_id=cubicle_state.__getattribute__("cubicle_id"),
                    occupied=cubicle_state.__getattribute__("occupied"),
                    toilet_roll_percentage=cubicle_state.__getattribute__(
                        "toilet_roll_percentage"
                    ),
                    updated_at=cubicle_state.__getattribute__("updated_at"),
                )
                for cubicle_state in cubicle_states
            ],
        )

    async def get_latest_mall_state(self, mall_id: int):
        toilets: Sequence[Toilet] = await self.toilets_service.get_toilets(
            mall_id=mall_id
        )
        latest_mall_state: LatestMallStateDto = LatestMallStateDto(
            mall_id=mall_id, toilets=[]
        )
        for toilet in toilets:
            toilet_state: LatestToiletStateDto = await self.get_latest_toilet_state(
                mall_id=mall_id, toilet_id=toilet.__getattribute__("id")
            )
            latest_mall_state.toilets.append(
                LatestToiletStateDto(
                    toilet_id=toilet.__getattribute__("id"),
                    cubicles=[
                        LatestCubicleStateDto(
                            cubicle_id=cubicle_state.__getattribute__("cubicle_id"),
                            occupied=cubicle_state.__getattribute__("occupied"),
                            toilet_roll_percentage=cubicle_state.__getattribute__(
                                "toilet_roll_percentage"
                            ),
                            updated_at=cubicle_state.__getattribute__("updated_at"),
                        )
                        for cubicle_state in toilet_state.cubicles
                    ],
                )
            )
        return latest_mall_state
