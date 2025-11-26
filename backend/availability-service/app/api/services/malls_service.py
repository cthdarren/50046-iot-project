from typing import Sequence
from schemas.request_dto.mall_request_dto import MallRequestDto
from fastapi import Depends
from core.exceptions import NotFoundException, DuplicateException
from db.database import get_db
from ..repo.malls_repo import MallsRepo
from db.models import Mall
from sqlalchemy.ext.asyncio import AsyncSession


class MallsService:
    def __init__(self, db: AsyncSession = Depends(get_db)) -> None:
        self.mall_repo = MallsRepo(db)

    async def get_mall_by_id(self, id: int) -> Mall:
        mall: Mall = await self.mall_repo.get_mall_by_id(id)
        if not mall:
            raise NotFoundException(detail="Mall not found.")
        return mall

    async def get_mall_by_name(self, mall_req_dto: MallRequestDto) -> Mall:
        mall: Mall = await self.mall_repo.get_mall_by_name(mall_req_dto)
        if not mall:
            raise NotFoundException(detail="Mall not found.")
        return mall

    async def get_malls(self) -> Sequence[Mall]:
        return await self.mall_repo.get_all()

    async def create_mall(self, name: str) -> Mall:
        if mall := await self.mall_repo.get_mall_by_name(MallRequestDto(name=name)):
            raise DuplicateException(detail="Mall already exists.")
        mall = Mall(name=name)
        return await self.mall_repo.create_mall(mall)

    async def update_mall(self, mall_id: int, name: str) -> Mall:
        mall = await self.get_mall_by_id(mall_id)
        dto = MallRequestDto(name=name)
        return await self.mall_repo.update_mall(mall, dto)

    async def delete_mall(self, mall_id: int) -> bool:
        if not await self.get_mall_by_id(mall_id):
            raise NotFoundException(detail="Mall not found.")
        return await self.mall_repo.delete_mall(mall_id)
