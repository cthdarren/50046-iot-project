from typing import List
from fastapi import Depends, HTTPException
from api.repo.toilets_repo import ToiletsRepo
from sqlalchemy.ext.asyncio import AsyncSession
from db.models import Toilet
from schemas.request_dto.toilet_request_dto import ToiletRequestDto
from db.database import get_db


class ToiletsService:
    def __init__(self, db: AsyncSession = Depends(get_db)) -> None:
        self.toilet_repo = ToiletsRepo(db)

    async def create_toilet(
        self, toilet_request_dto: ToiletRequestDto
    ) -> Toilet | HTTPException:
        return Toilet()

    async def get_toilets(self, mall_id: int) -> List[Toilet]:
        return []

    async def get_toilet(self, toilet_id: int) -> Toilet | HTTPException:
        return Toilet()

    async def update_toilet(
        self,
        toilet_id: int,
        toilet_req_dto: ToiletRequestDto,
    ) -> Toilet | HTTPException:
        return Toilet()

    async def delete_toilet(self, toilet_id: int) -> bool | HTTPException:
        return False
