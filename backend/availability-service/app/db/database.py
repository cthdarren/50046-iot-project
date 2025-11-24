from sqlalchemy import Engine
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    create_async_engine,
    async_sessionmaker
)
from core.config import Settings

if not Settings.DATABASE_URL:
    raise ValueError("DATABASE_URL is not set in .env file.")

engine: Engine = create_async_engine(
    url=Settings.DATABASE_URL, 
    echo=False, 
    future=True
)

SessionLocal: async_sessionmaker[AsyncSession] = async_sessionmaker(
    bind=engine, 
    autoflush=False, 
    bind=engine
)

async def get_db():
    async with SessionLocal() as session:
        yield session

