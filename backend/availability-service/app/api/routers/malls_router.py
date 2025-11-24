from typing import List
from fastapi import APIRouter, Depends
from db.models import Mall
from schemas.response_dto.mall_dto import MallDto
from schemas.response_dto.common import APIError, ErrorResponse, SuccessResponse
from ..services.malls_service import MallService

router = APIRouter(prefix="/malls")


@router.get("/", response_model=SuccessResponse | ErrorResponse)
def get_malls(service: MallService = Depends()):
    malls: List[Mall] = service.get_malls()
    return SuccessResponse(
        data=[MallDto.model_validate(mall) for mall in malls]
    )


@router.get("/{mall_id}", response_model=SuccessResponse | ErrorResponse)
def get_mall(mall_id: int, service: MallService = Depends()):
    if mall := service.get_mall_by_id(mall_id):
        return SuccessResponse(data=MallDto.model_validate(mall))
    return ErrorResponse(
        error=APIError(code="404", message="No mall found for request.")
    )


@router.post("/")
def create_mall(name: str, service: MallService = Depends()):
    pass


@router.put("/{mall_id}")
def update_mall():
    pass


@router.delete("/{mall_id}")
def delete_mall():
    pass
