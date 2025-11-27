from db.database import get_db
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from ..repo.cubicles_repo import CubiclesRepo
from ..services.toilets_service import ToiletsService
from schemas.request_dto.cubicle_request_dto import CubicleRequestDto
from schemas.response_dto.cubicle_dto import CubicleDto
from core.exceptions import NotFoundException
from typing import Sequence
from db.models import Cubicle

class CubiclesService:
    def __init__(self, toilet_service: ToiletsService = Depends(), db: AsyncSession = Depends(get_db) ):
        self.cubicles_repo = CubiclesRepo(db)
        self.toilet_service = toilet_service

    async def create_cubicle(self, mall_id: int,cubicle_req_dto: CubicleRequestDto) -> CubicleDto:
        toilet = await self.toilet_service.get_toilet(toilet_id=cubicle_req_dto.toilet_id, mall_id=mall_id)
        if not toilet:
            raise NotFoundException(detail="Toilet not found.")
        new_cubicle: Cubicle = await self.cubicles_repo.create_cubicle(cubicle_req_dto)
        return CubicleDto.from_orm(new_cubicle)
    
    async def get_cubicles(self, mall_id: int, toilet_id: int) -> Sequence[CubicleDto]:
        toilet = await self.toilet_service.get_toilet(toilet_id=toilet_id, mall_id=mall_id)
        if not toilet:
            raise NotFoundException(detail="Toilet not found.")
        return [CubicleDto.from_orm(cubicle) for cubicle in await self.cubicles_repo.get_cubicles(toilet_id)]
    
    async def get_cubicle(self, mall_id: int, toilet_id: int, cubicle_id: int) -> CubicleDto:
        if not await self.toilet_service.get_toilet(toilet_id=toilet_id, mall_id=mall_id):
            raise NotFoundException(detail="Toilet not found.")
        cubicle: Cubicle | None = await self.cubicles_repo.get_cubicle(cubicle_id)
        if not cubicle:
            raise NotFoundException("Cubicle not found.")
        return CubicleDto.from_orm(cubicle)
    
    async def update_cubicle(self, mall_id: int, toilet_id: int, cubicle_id: int, cubicle_req_dto: CubicleRequestDto) -> CubicleDto:
        cubicle_dto: CubicleDto = await self.get_cubicle(mall_id, toilet_id, cubicle_id)
        if not cubicle_dto:
            raise NotFoundException(detail="Cubicle not found.")
        new_toilet = await self.toilet_service.get_toilet(toilet_id=cubicle_req_dto.toilet_id, mall_id=mall_id)
        if not new_toilet:
            raise NotFoundException(detail=f"Toilet not found for toilet_id: {cubicle_req_dto.toilet_id}.")
        return CubicleDto.from_orm(await self.cubicles_repo.update_cubicle(cubicle_id=cubicle_id, cubicle_req_dto=cubicle_req_dto))
    
    async def delete_cubicle(self, mall_id: int, toilet_id: int, cubicle_id: int) -> bool:
        cubicle = await self.get_cubicle(mall_id, toilet_id, cubicle_id)
        if not cubicle:
            raise NotFoundException(detail="Cubicle not found.")
        return await self.cubicles_repo.delete_cubicle(cubicle_id)