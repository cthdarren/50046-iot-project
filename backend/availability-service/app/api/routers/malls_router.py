from typing import List, Sequence
from fastapi import APIRouter, Depends
from schemas.request_dto.mall_request_dto import MallRequestDto
from db.models import Mall
from schemas.response_dto.mall_dto import MallDto
from schemas.response_dto.common import SuccessResponse
from ..services.malls_service import MallsService

router = APIRouter(prefix="/malls")


@router.get("/", response_model=List[MallDto])
async def get_malls(service: MallsService = Depends()) -> List[MallDto]:
    malls: Sequence[Mall] = await service.get_malls()
    return [MallDto.model_validate(mall) for mall in malls]


@router.get("/{mall_id}", response_model=MallDto)
async def get_mall(mall_id: int, service: MallsService = Depends()) -> MallDto:
    mall = await service.get_mall_by_id(mall_id)
    return MallDto.model_validate(mall)


@router.post("/", response_model=MallDto)
async def create_mall(
    req_dto: MallRequestDto, service: MallsService = Depends()
) -> MallDto:
    mall: Mall = await service.create_mall(req_dto.name)
    return MallDto.model_validate(mall)


@router.put("/{mall_id}", response_model=MallDto)
async def update_mall(
    mall_id: int, req_dto: MallRequestDto, service: MallsService = Depends()
) -> MallDto:
    updated_mall: Mall = await service.update_mall(mall_id, req_dto.name)
    return MallDto.model_validate(updated_mall)


@router.delete("/{mall_id}", response_model=SuccessResponse)
async def delete_mall(
    mall_id: int, service: MallsService = Depends()
) -> SuccessResponse:
    await service.delete_mall(mall_id)
    return SuccessResponse(data="Successfully deleted mall.")
