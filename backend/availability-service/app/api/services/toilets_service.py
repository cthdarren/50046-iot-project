from typing import Sequence, Optional
from api.repo.toilets_repo import ToiletsRepo
from sqlalchemy.ext.asyncio import AsyncSession
from shared.core.exceptions import InternalServerErrorException, NotFoundException
from db.models import Toilet
from schemas.request_dto.toilet_request_dto import ToiletRequestDto
from db.database import get_db
from api.repo.malls_repo import MallsRepo
from fastapi import Depends


class ToiletsService:
    def __init__(self, db: AsyncSession = Depends(get_db)) -> None:
        self.toilet_repo = ToiletsRepo(db)
        self.mall_repo = MallsRepo(db)

    async def create_toilet(self, mall_id: int, toilet_request_dto: ToiletRequestDto) -> Toilet:
        if not await self.mall_repo.get_mall_by_id(mall_id):
            raise NotFoundException(detail="Mall not found.")
        return await self.toilet_repo.create_toilet(mall_id, toilet_request_dto)

    async def get_toilets(self, mall_id: int) -> Sequence[Toilet]:
        if not await self.mall_repo.get_mall_by_id(mall_id):
            raise NotFoundException(detail="Mall not found.")
        return await self.toilet_repo.get_toilets(mall_id)

    async def get_toilet(self, mall_id:int, toilet_id: int) -> Toilet:
        if not await self.mall_repo.get_mall_by_id(mall_id):
            raise NotFoundException(detail="Mall not found.")
        toilet: Toilet = await self.toilet_repo.get_toilet(toilet_id, mall_id)
        if not toilet:
            raise NotFoundException(detail="Toilet not found.")
        return toilet
    
    async def get_toilets_by_fields(self, mall_id: int, gender: Optional[str], level: Optional[str], description: Optional[str]) -> Sequence[Toilet]:
        if not await self.mall_repo.get_mall_by_id(mall_id):
            raise NotFoundException(detail="Mall not found.")
        return await self.toilet_repo.get_toilets_by_fields(mall_id, gender, level, description)

    async def update_toilet(
        self,
        mall_id: int,
        toilet_id: int,
        toilet_req_dto: ToiletRequestDto,
    ) -> Toilet:
        if not await self.mall_repo.get_mall_by_id(mall_id):
            raise NotFoundException(detail="Mall not found.")
        toilet: Toilet = await self.toilet_repo.get_toilet(toilet_id, mall_id)
        if not toilet:
            raise NotFoundException(detail="Toilet not found.")
        updated_toilet: Toilet = await self.toilet_repo.update_toilet(
            toilet, toilet_req_dto
        )
        if not updated_toilet:
            raise InternalServerErrorException(
                detail="Unable to update toilet information."
            )
        return updated_toilet

    async def delete_toilet(self, mall_id: int, toilet_id: int) -> bool:
        if not await self.toilet_repo.get_toilet(toilet_id, mall_id):
            raise NotFoundException(detail="Toilet not found.")
        return await self.toilet_repo.delete_toilet(toilet_id, mall_id)
