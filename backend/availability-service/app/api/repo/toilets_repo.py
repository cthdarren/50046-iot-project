from schemas.enum.toilet_enum import Gender
from sqlalchemy.ext.asyncio import AsyncSession

class ToiletsRepo:
    def __init__(self, db):
        self.db = db
        
    async def create_toilet(self, label: str, gender: Gender, db_session: AsyncSession):
        pass