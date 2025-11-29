from fastapi import FastAPI
from api.routers.analytics_router import router as analytics_router

app = FastAPI()

app.include_router(analytics_router)

@app.get("/")
def read_root():
    return {"Analytics service is running."}
