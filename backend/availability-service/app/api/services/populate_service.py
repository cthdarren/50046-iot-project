from fastapi import Depends
from api.services.malls_service import MallsService
from api.services.toilets_service import ToiletsService
from api.services.cubicles_service import CubiclesService
from db.models import Mall
from db.models import Toilet
from db.models import Cubicle
from db.models import CubicleEvent
from api.repo.populate_repo import PopulateRepo
from schemas.request_dto.toilet_request_dto import ToiletRequestDto
from schemas.request_dto.cubicle_request_dto import CubicleRequestDto
from schemas.enum.toilet_enum import Gender
from shared.schemas.state import CubicleEventDto
from typing import List, Sequence
from datetime import datetime, timedelta
import numpy as np
from db.database import get_db
from sqlalchemy.ext.asyncio import AsyncSession

class PopulateService:
    def __init__(
        self,
        malls_service: MallsService = Depends(),
        toilets_service: ToiletsService = Depends(),
        cubicles_service: CubiclesService = Depends(),
        db: AsyncSession = Depends(get_db),
    ):
        self.malls_service = malls_service
        self.toilets_service = toilets_service
        self.cubicles_service = cubicles_service
        self.populate_repo = PopulateRepo(db)
        self.db = db

    async def populate_malls(self, count: int = 50) -> List[Mall]:
        created_malls_list: List[Mall] = []
        for i in range(count):
            created_mall: Mall = await self.malls_service.create_mall(name=f"Mall {i}")
            created_malls_list.append(created_mall)
        return created_malls_list

    async def populate_toilets(
        self, mall_ids: list[int], count: int = 50
    ) -> List[Toilet]:
        created_toilets_list: List[Toilet] = []
        for mall_id in mall_ids:
            for i in range(count):
                toilet_req_dto: ToiletRequestDto = ToiletRequestDto(
                    description=f"Toilet {i}",
                    gender=Gender.male if i % 2 == 0 else Gender.female,
                    level=f"Level {i % 5}",
                )
                created_toilet: Toilet = await self.toilets_service.create_toilet(
                    mall_id=mall_id,
                    toilet_request_dto=toilet_req_dto,
                )
                created_toilets_list.append(created_toilet)
        return created_toilets_list

    async def populate_cubicles(
        self, toilet_list: list[Toilet], count: int = 50
    ) -> List[Cubicle]:
        created_cubicles_list: List[Cubicle] = []
        for toilet in toilet_list:
            for i in range(count):
                cubicle_req_dto: CubicleRequestDto = CubicleRequestDto(
                    toilet_id=toilet.__getattribute__("id"),
                )
                created_cubicle: Cubicle = await self.cubicles_service.create_cubicle(
                        mall_id=toilet.__getattribute__("mall_id"),
                        cubicle_req_dto=cubicle_req_dto,
                    )
                created_cubicles_list.append(created_cubicle)
        return created_cubicles_list

    async def populate_events(self, cubicle_ids: list[int], count: int = 50, mean_minutes: int = 15, std_minutes: int = 15) -> Sequence[CubicleEvent]:
        deltas = np.random.normal(mean_minutes, std_minutes, size=count)
        timestamps = [datetime.now() - timedelta(minutes= max(0, abs(delta))) for delta in deltas]
        cubicle_events: list[CubicleEvent] = []
        for cubicle_id in cubicle_ids:
            for i in range(count):
                cubicle_event: CubicleEvent = CubicleEvent(
                    cubicle_id=cubicle_id,
                    occupied=True if i % 2 == 0 else False,
                    toilet_roll_percentage=int((i % 7) * 10),
                    timestamp=timestamps[i],
                )
                cubicle_events.append(cubicle_event)
        created_events: Sequence[CubicleEvent] = await self.populate_repo.create_cubicle_events(
            cubicle_events=cubicle_events,
        )
        return created_events
