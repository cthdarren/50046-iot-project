from fastapi import FastAPI
from shared.core.exceptions import ApiException, exception_handler

from api.routers.analytics_router import router as analytics_router

app = FastAPI(title="Analytics Service", root_path="/analytics")

app.include_router(analytics_router)


@app.get("/")
def read_root():
    return {"message": "Analytics service is running."}


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "healthy"}


app.add_exception_handler(ApiException, exception_handler)
