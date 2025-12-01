from fastapi import FastAPI
from api.routers.analytics_router import router as analytics_router
from shared.core.exceptions import ApiException, exception_handler

app = FastAPI()

app.include_router(analytics_router)

@app.get("/")
def read_root():
    return {"Analytics service is running."}

app.add_exception_handler(ApiException, exception_handler)
