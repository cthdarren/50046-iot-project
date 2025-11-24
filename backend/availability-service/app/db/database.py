from sqlalchemy.ext.asyncio import (
    AsyncSession,
    AsyncEngine,
    create_async_engine,
    async_sessionmaker,
)
from core.config import settings

if not settings.DATABASE_URL:
    raise ValueError("DATABASE_URL is not set in .env file.")

engine: AsyncEngine = create_async_engine(
    url=settings.DATABASE_URL, echo=False, future=True
)

SessionLocal: async_sessionmaker[AsyncSession] = async_sessionmaker(
    bind=engine, autoflush=False
)


async def get_db():
    async with SessionLocal() as session:
        yield session
