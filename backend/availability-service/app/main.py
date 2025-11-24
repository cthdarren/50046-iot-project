from fastapi import FastAPI
from api.routers.malls_router import router as  malls_router

app = FastAPI(title="Availability Service")
app.include_router(malls_router)

@app.get("/")
def root() -> dict[str, str]:
    return {"message": "Availability service is running."}
