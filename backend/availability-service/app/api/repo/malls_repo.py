from typing import Literal, Sequence
from sqlalchemy import delete, select, insert
from sqlalchemy.orm import selectinload
from schemas.request_dto.mall_request_dto import MallRequestDto
from db.models import Mall
from sqlalchemy.ext.asyncio import AsyncSession


class MallsRepo:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_mall(self, req_dto: MallRequestDto) -> Mall:
        mall: Mall = Mall(
            name=req_dto.name,
        )
        self.db.add(mall)
        await self.db.flush()
        await self.db.commit()
        stmt = select(Mall).where(Mall.id == mall.id).options(selectinload(Mall.toilets))
        result = await self.db.execute(stmt)
        return result.scalar_one()

    async def get_mall_by_id(self, id: int) -> Mall | None:
        statement = (
            select(Mall).where(Mall.id == id).options(selectinload(Mall.toilets))
        )
        result = await self.db.execute(statement)
        return result.scalar_one_or_none()

    async def get_mall_by_name(self, data: MallRequestDto) -> Mall | None:
        statement = (
            select(Mall)
            .where(Mall.name == data.name)
            .options(selectinload(Mall.toilets))
            .limit(1)
        )
        result = await self.db.execute(statement)
        return result.scalar_one_or_none()

    async def get_all(self) -> Sequence[Mall]:
        result = await self.db.execute(select(Mall).options(selectinload(Mall.toilets)))
        return result.scalars().all()

    async def update_mall(self, mall: Mall, data: MallRequestDto) -> Mall:
        for k, v in data.model_dump(exclude_unset=True).items():
            setattr(mall, k, v)
        await self.db.commit()
        await self.db.refresh(mall, attribute_names=["toilets"])
        return mall

    async def delete_mall(self, id: int) -> Literal[True]:
        statement = delete(Mall).where(Mall.id == id)
        await self.db.execute(statement)
        await self.db.commit()
        return True
