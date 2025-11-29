from sqlalchemy.ext.asyncio import AsyncSession
from shared.core.period import PeriodRange, Period
from db.models import CubicleState, Cubicle, Toilet
from sqlalchemy import select
from typing import Sequence
from sqlalchemy.orm import joinedload


class EventsRepo:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_events(
        self,
        period_range: PeriodRange | None = None,
        period: Period | None = None,
        mall_id: int | None = None,
        toilet_id: int | None = None,
        cubicle_id: int | None = None,
    ):
        pass

    async def get_latest_cubicle_state(self, cubicle_id: int) -> CubicleState | None:
        stmt = select(CubicleState).where(CubicleState.cubicle_id == cubicle_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_latest_toilet_state(self, toilet_id: int) -> Sequence[CubicleState]:
        stmt = (
            select(CubicleState)
            .join(Cubicle, CubicleState.cubicle_id == Cubicle.id)
            .where(Cubicle.toilet_id == toilet_id)
            .options(joinedload(CubicleState.cubicle))
        )
        results = await self.db.execute(stmt)
        return results.scalars().unique().all()

    async def get_latest_mall_state(self, mall_id: int) -> Sequence[CubicleState]:
        stmt = (
            select(CubicleState)
            .join(Cubicle, CubicleState.cubicle_id == Cubicle.id)
            .join(Toilet, Cubicle.toilet_id == Toilet.id)
            .where(Toilet.mall_id == mall_id)
            .options(joinedload(CubicleState.cubicle))
        )
        results = await self.db.execute(stmt)
        return results.scalars().unique().all()
