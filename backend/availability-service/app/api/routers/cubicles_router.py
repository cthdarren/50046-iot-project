from fastapi import APIRouter, Depends
from schemas.request_dto.cubicle_request_dto import CubicleRequestDto
from schemas.response_dto.cubicle_dto import CubicleDto
from ..services.cubicles_service import CubiclesService
from schemas.response_dto.common import SuccessResponse
from typing import Sequence
from schemas.response_dto.cubicles_list_dto import CubiclesListDto

router = APIRouter(prefix="/malls/{mall_id}/toilets/{toilet_id}/cubicles")

@router.post("/")
async def create_cubicle(mall_id: int, cubicle_req_dto: CubicleRequestDto, cubicles_service: CubiclesService = Depends()) -> CubicleDto:
    cubicle: CubicleDto = await cubicles_service.create_cubicle(mall_id, cubicle_req_dto)
    return cubicle

@router.get("/{cubicle_id}")
async def get_cubicle(mall_id: int, toilet_id: int, cubicle_id: int, cubicles_service: CubiclesService = Depends()) -> CubicleDto:
    cubicle: CubicleDto = await cubicles_service.get_cubicle(mall_id, toilet_id,cubicle_id)
    return cubicle

@router.get("/")
async def get_cubicles(mall_id: int, toilet_id: int, cubicles_service: CubiclesService = Depends()) -> CubiclesListDto:
    cubicles: Sequence[CubicleDto] = await cubicles_service.get_cubicles(mall_id, toilet_id)
    return CubiclesListDto(toilet_id=toilet_id, cubicles=cubicles)

@router.put("/{cubicle_id}")
async def update_cubicle(mall_id: int, toilet_id: int, cubicle_id: int, cubicle_req_dto: CubicleRequestDto, cubicles_service: CubiclesService = Depends()) -> CubicleDto:
    cubicle: CubicleDto = await cubicles_service.update_cubicle(mall_id, toilet_id, cubicle_id, cubicle_req_dto)
    return cubicle

@router.delete("/{cubicle_id}")
async def delete_cubicle(mall_id: int, toilet_id: int, cubicle_id: int, cubicles_service: CubiclesService = Depends()) -> SuccessResponse:
    await cubicles_service.delete_cubicle(mall_id, toilet_id, cubicle_id)
    return SuccessResponse(data="Successfully deleted cubicle.")
