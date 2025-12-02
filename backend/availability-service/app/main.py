from contextlib import asynccontextmanager

from fastapi import FastAPI
from shared.core.exceptions import ApiException, exception_handler

from api.routers.cubicles_router import router as cubicles_router
from api.routers.events_router import router as events_router
from api.routers.malls_router import router as malls_router
from api.routers.toilets_router import router as toilets_router
from db.database import engine, wait_for_db
from db.models import Base
from fastapi.middleware.cors import CORSMiddleware


@asynccontextmanager
async def lifespan(app: FastAPI):
    await wait_for_db()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        print("Database tables created.")
    yield


app = FastAPI(
    title="Availability Service", lifespan=lifespan, root_path="/availability"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(malls_router)
app.include_router(toilets_router)
app.include_router(cubicles_router)
app.include_router(events_router)
app.add_exception_handler(ApiException, exception_handler)


@app.get("/")
def root() -> dict[str, str]:
    return {"message": "Availability service is running."}


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "healthy"}
