from typing import AsyncGenerator
from db.database import get_db
from sqlalchemy.ext.asyncio import AsyncSession

class MallsRepo():
    def __init__(self) -> None:
        self.db: AsyncGenerator[AsyncSession] = get_db()