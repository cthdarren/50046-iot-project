import asyncio
from typing import AsyncIterator
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    AsyncEngine,
    create_async_engine,
    async_sessionmaker,
)
from core.config import settings

configs = [settings.DB_USER, settings.DB_PASSWORD, settings.DB_HOST, settings.DB_PORT, settings.DB_NAME]

for e in configs:
    if not e:
        raise ValueError(f"{e=} is not set in .env file.")
    

DATABASE_URL = f"postgresql+asyncpg://{settings.DB_USER}:{settings.DB_PASSWORD}@{settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}"


engine: AsyncEngine = create_async_engine(
    url=DATABASE_URL,
    echo=True,
    future=True,
    pool_pre_ping=True,
)

async def wait_for_db():
    import asyncpg
    retries = 5
    for i in range(retries):
        try:
            conn = await asyncpg.connect(DATABASE_URL)
            await conn.close()
            return
        except Exception:
            print("DB not ready, retrying...")
            await asyncio.sleep(2)

SessionLocal: async_sessionmaker[AsyncSession] = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    autoflush=False,
    expire_on_commit=False,
)


async def get_db() -> AsyncIterator[AsyncSession]:
    async with SessionLocal() as session:
        yield session
