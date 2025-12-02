from db.database import get_db
from ..repo.events_repo import EventsRepo
from shared.core.period import PeriodRange
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends
from typing import Sequence, Optional, List
from db.models import CubicleEvent, CubicleState, Cubicle, Toilet
from api.services.toilets_service import ToiletsService
from api.services.cubicles_service import CubiclesService
from api.services.malls_service import MallsService
from shared.core.exceptions import NotFoundException
from shared.schemas.latest_state import (
    LatestCubicleStateDto,
    LatestToiletStateDto,
    LatestMallStateDto,
)
from shared.schemas.state import (
    FilteredCubicleEventDto,
    FilteredToiletEventDto,
    FilteredMallEventDto,
    ToiletEventDto,
    CubicleEventDto,
    CubicleEventListDto,
)
from datetime import datetime
from typing import Union


class EventsService:

    def __init__(
        self,
        db: AsyncSession = Depends(get_db),
        toilets_service: ToiletsService = Depends(),
        cubicles_service: CubiclesService = Depends(),
        malls_service: MallsService = Depends(),
    ) -> None:
        self.events_repo = EventsRepo(db)
        self.toilets_service = toilets_service
        self.cubicles_service = cubicles_service
        self.malls_service = malls_service

    async def get_latest_cubicle_state(
        self, mall_id: int, toilet_id: int, cubicle_id: int
    ) -> LatestCubicleStateDto:
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
        if not (toilet := await self.toilets_service.get_toilet(
            mall_id=mall_id, toilet_id=toilet_id
        )):
            raise NotFoundException(detail="Toilet not found.")
        cubicle_states: Sequence[CubicleState] = (
            await self.events_repo.get_latest_toilet_state(toilet_id)
        )
        return LatestToiletStateDto(
            toilet_id=toilet_id,
            level=toilet.__getattribute__("level"),
            gender=toilet.__getattribute__("gender"),
            description=toilet.__getattribute__("description"),
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

    async def get_latest_mall_state(self, mall_id: int) -> LatestMallStateDto:
        if not (mall := await self.malls_service.get_mall_by_id(id=mall_id)):
            raise NotFoundException(detail="Mall not found.")
        toilets: Sequence[Toilet] = await self.toilets_service.get_toilets(
            mall_id=mall_id
        )
        latest_mall_state: LatestMallStateDto = LatestMallStateDto(
            mall_id=mall_id, name=mall.__getattribute__("name"), toilets=[]
        )
        for toilet in toilets:
            toilet_state: LatestToiletStateDto = await self.get_latest_toilet_state(
                mall_id=mall_id, toilet_id=toilet.__getattribute__("id")
            )
            latest_mall_state.toilets.append(
                LatestToiletStateDto(
                    toilet_id=toilet.__getattribute__("id"),
                    level=toilet.__getattribute__("level"),
                    gender=toilet.__getattribute__("gender"),
                    description=toilet.__getattribute__("description"),
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

    async def get_events(
        self,
        mall_id: int,
        toilet_id: Optional[int] = None,
        cubicle_id: Optional[int] = None,
        period_range: PeriodRange = PeriodRange(
            start_date=datetime.now(), end_date=datetime.now()
        ),
    ) -> Union[FilteredCubicleEventDto, FilteredToiletEventDto, FilteredMallEventDto]:

        if toilet_id:
            if cubicle_id:
                cubicle_states: FilteredCubicleEventDto = (
                    await self.get_filtered_cubicle_events(
                        cubicle_id=cubicle_id,
                        period_range=period_range,
                    )
                )
                return cubicle_states
            toilet_states: FilteredToiletEventDto = (
                await self.get_filtered_toilet_events(
                    mall_id=mall_id,
                    toilet_id=toilet_id,
                    period_range=period_range,
                )
            )
            return toilet_states
        mall_states: FilteredMallEventDto = await self.get_filtered_mall_events(
            mall_id=mall_id,
            period_range=period_range,
        )
        return mall_states

    async def get_filtered_cubicle_events(
        self, cubicle_id: int, period_range: PeriodRange
    ) -> FilteredCubicleEventDto:
        cubicle_events: Sequence[CubicleEvent] = (
            await self.events_repo.get_filtered_cubicle_events(
                cubicle_id=cubicle_id,
                period_range=period_range,
            )
        )
        cubicle_events_dto: List[CubicleEventDto] = []
        for cubicle_event in cubicle_events:
            cubicle_events_dto.append(
                CubicleEventDto(
                    occupied=cubicle_event.__getattribute__("occupied"),
                    toilet_roll_percentage=cubicle_event.__getattribute__(
                        "toilet_roll_percentage"
                    ),
                    updated_at=cubicle_event.__getattribute__("timestamp"),
                )
            )
        return FilteredCubicleEventDto(
            cubicle_id=cubicle_id,
            events=cubicle_events_dto,
            period_range=period_range,
        )

    async def get_filtered_toilet_events(
        self,
        mall_id: int,
        toilet_id: int,
        period_range: PeriodRange,
    ) -> FilteredToiletEventDto:
        cubicles: Sequence[Cubicle] = await self.cubicles_service.get_cubicles(
            mall_id=mall_id, toilet_id=toilet_id
        )
        filtered_toilet_event_dto: FilteredToiletEventDto = FilteredToiletEventDto(
            toilet_id=toilet_id,
            cubicles=[],
            period_range=period_range,
        )

        for cubicle in cubicles:
            cubicle_events: FilteredCubicleEventDto = (
                await self.get_filtered_cubicle_events(
                    cubicle_id=cubicle.__getattribute__("id"),
                    period_range=period_range,
                )
            )
            filtered_toilet_event_dto.cubicles.append(
                CubicleEventListDto(
                    cubicle_id=cubicle.__getattribute__("id"),
                    events=cubicle_events.events,
                )
            )

        return filtered_toilet_event_dto

    async def get_filtered_mall_events(
        self, mall_id: int, period_range: PeriodRange
    ) -> FilteredMallEventDto:
        toilets: Sequence[Toilet] = await self.toilets_service.get_toilets(
            mall_id=mall_id
        )
        latest_mall_event: FilteredMallEventDto = FilteredMallEventDto(
            mall_id=mall_id, toilets=[], period_range=period_range
        )
        for toilet in toilets:
            toilet_events: FilteredToiletEventDto = (
                await self.get_filtered_toilet_events(
                    toilet_id=toilet.__getattribute__("id"),
                    period_range=period_range,
                    mall_id=mall_id,
                )
            )
            latest_mall_event.toilets.append(
                ToiletEventDto(
                    toilet_id=toilet.__getattribute__("id"),
                    cubicles=toilet_events.cubicles,
                )
            )
        return latest_mall_event
