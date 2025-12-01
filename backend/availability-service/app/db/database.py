import asyncio
from typing import AsyncIterator

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from core.config import settings

configs = [
    settings.DB_USER,
    settings.DB_PASSWORD,
    settings.DB_HOST,
    settings.DB_PORT,
    settings.DB_NAME,
]

for e in configs:
    if not e:
        raise ValueError(f"{e=} is not set in .env file.")


DATABASE_URL = f"postgresql+asyncpg://{settings.DB_USER}:{settings.DB_PASSWORD}@{settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}"
DATABASE_URL_ASYNCPG = f"postgresql://{settings.DB_USER}:{settings.DB_PASSWORD}@{settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}"

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
            print(
                f"Attempting to connect to DB at {settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME} (attempt {i + 1}/{retries})"
            )
            conn = await asyncpg.connect(DATABASE_URL_ASYNCPG)
            await conn.close()
            print("Successfully connected to database!")
            return
        except Exception as e:
            print(f"DB not ready, retrying... Error: {str(e)}")
            await asyncio.sleep(2)
    raise Exception(f"Failed to connect to database after {retries} attempts")


SessionLocal: async_sessionmaker[AsyncSession] = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    autoflush=False,
    expire_on_commit=False,
)


async def get_db() -> AsyncIterator[AsyncSession]:
    async with SessionLocal() as session:
        yield session
