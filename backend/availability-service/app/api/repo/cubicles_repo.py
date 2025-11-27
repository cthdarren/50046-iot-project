from db.models import Cubicle, CubicleState, CubicleEvent
from sqlalchemy import select, delete
from sqlalchemy.orm import selectinload, joinedload
from schemas.request_dto.cubicle_request_dto import CubicleRequestDto
from typing import Sequence
from sqlalchemy.ext.asyncio import AsyncSession


class CubiclesRepo:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_cubicle(self, cubicle_req_dto: CubicleRequestDto) -> Cubicle:
        new_cubicle = Cubicle(
            toilet_id=cubicle_req_dto.toilet_id,
        )
        if new_cubicle.cubicle_state is None:
            new_cubicle.cubicle_state = CubicleState(
                cubicle_id=new_cubicle.id,
                occupied=False,
                toilet_roll_percentage=0,
            )
        self.db.add(new_cubicle)
        await self.db.flush()
        await self.db.commit()
        stmt = (
            select(Cubicle)
            .where(Cubicle.id == new_cubicle.id)
            .options(
                selectinload(Cubicle.cubicle_state),
            )
        )
        result = await self.db.execute(stmt)
        return result.scalar_one()

    async def get_cubicles(self, toilet_id: int) -> Sequence[Cubicle]:
        stmt = (
            select(Cubicle)
            .where(Cubicle.toilet_id == toilet_id)
            .options(
                joinedload(Cubicle.cubicle_state),
            )
        )
        result = await self.db.execute(stmt)
        cubicles = result.scalars().all()
        for cubicle in cubicles:
            if cubicle.cubicle_state:
                await self.db.refresh(cubicle.cubicle_state)
        return cubicles

    async def get_cubicle(self, toilet_id: int, cubicle_id: int) -> Cubicle | None:
        stmt = (
            select(Cubicle)
            .where(Cubicle.id == cubicle_id, Cubicle.toilet_id == toilet_id)
            .options(
                joinedload(Cubicle.cubicle_state),
            )
        )
        result = await self.db.execute(stmt)
        cubicle = result.scalar_one_or_none()
        if cubicle and cubicle.cubicle_state:
            await self.db.refresh(cubicle.cubicle_state)
        return cubicle

    async def update_cubicle(
        self, cubicle: Cubicle, cubicle_req_dto: CubicleRequestDto
    ) -> Cubicle:
        for key, value in cubicle_req_dto.model_dump(exclude_unset=True).items():
            setattr(cubicle, key, value)
        self.db.add(cubicle)
        await self.db.flush()
        await self.db.commit()
        await self.db.refresh(cubicle, attribute_names=["cubicle_state"])
        return cubicle

    async def delete_cubicle(self, cubicle_id: int) -> bool:
        statement_cubicle_state = delete(CubicleState).where(
            CubicleState.cubicle_id == cubicle_id
        )
        statement = delete(Cubicle).where(Cubicle.id == cubicle_id)
        await self.db.execute(statement_cubicle_state)
        await self.db.execute(statement)
        await self.db.commit()
        return True

    async def get_cubicle_state(self, cubicle_id: int) -> CubicleState | None:
        stmt = select(CubicleState).where(CubicleState.cubicle_id == cubicle_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_latest_cubicle_event(self, cubicle_id: int) -> CubicleEvent | None:
        stmt = (
            select(CubicleEvent)
            .where(CubicleEvent.cubicle_id == cubicle_id)
            .order_by(CubicleEvent.timestamp.desc())
            .limit(1)
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
