from main import app
from fastapi import APIRouter
from services.malls_service import MallService

router = APIRouter(prefix="/malls")

@router.get("/")
def get_malls():
    pass

@router.get("/{mall_id}")
def get_mall(mall_id: int):
    pass

@router.post("/")
def create_mall():
    pass

@router.put("/{mall_id}")
def update_mall():
    pass

@router.delete("/{mall_id}")
def delete_mall():
    pass

