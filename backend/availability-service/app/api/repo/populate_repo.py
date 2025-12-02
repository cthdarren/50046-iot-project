from db.models import CubicleEvent
from shared.schemas.state import CubicleEventDto
from typing import List, Sequence
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select


class PopulateRepo:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_cubicle_events(
        self, cubicle_events: List[CubicleEvent]
    ) -> Sequence[CubicleEvent]:
        for cubicle_event in cubicle_events:
            self.db.add(cubicle_event)
        await self.db.flush()
        await self.db.commit()
        select_stmt = select(CubicleEvent).where(
            CubicleEvent.cubicle_id.in_(
                [
                    cubicle_event.__getattribute__("id")
                    for cubicle_event in cubicle_events
                ]
            )
        )
        result = await self.db.execute(select_stmt)
        result_cubicle_events: Sequence[CubicleEvent] = result.scalars().all()
        return result_cubicle_events
