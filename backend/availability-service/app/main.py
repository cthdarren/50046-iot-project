from fastapi import FastAPI
from api.routers.malls_router import router as malls_router
from api.routers.toilets_router import router as toilets_router
from contextlib import asynccontextmanager
from core.exceptions import ApiException, NotFoundException, exception_handler
from db.database import engine
from db.models import Base


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        yield

app = FastAPI(title="Availability Service", lifespan=lifespan)
app.include_router(malls_router)
app.include_router(toilets_router)
app.add_exception_handler(ApiException, exception_handler)


@app.get("/")
def root() -> dict[str, str]:
    return {"message": "Availability service is running."}
