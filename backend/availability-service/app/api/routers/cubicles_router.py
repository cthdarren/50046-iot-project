from fastapi import APIRouter, Depends
from schemas.request_dto.cubicle_request_dto import CubicleRequestDto
from schemas.response_dto.cubicle_dto import CubicleDto
from ..services.cubicles_service import CubiclesService
from schemas.response_dto.common import SuccessResponse
from typing import Sequence
from schemas.response_dto.cubicles_list_dto import CubiclesListDto
from db.models import Cubicle

router = APIRouter(prefix="/malls/{mall_id}/toilets/{toilet_id}/cubicles")


@router.post("/")
async def create_cubicle(
    mall_id: int,
    cubicle_req_dto: CubicleRequestDto,
    cubicles_service: CubiclesService = Depends(),
) -> CubicleDto:
    cubicle: Cubicle = await cubicles_service.create_cubicle(mall_id, cubicle_req_dto)
    return CubicleDto.model_validate(cubicle)


@router.get("/{cubicle_id}")
async def get_cubicle(
    mall_id: int,
    toilet_id: int,
    cubicle_id: int,
    cubicles_service: CubiclesService = Depends(),
) -> CubicleDto:
    cubicle: Cubicle = await cubicles_service.get_cubicle(
        mall_id, toilet_id, cubicle_id
    )
    print(
        f' cubicle_id: {cubicle.__getattribute__("id")}, toilet_id: {cubicle.__getattribute__("toilet_id")}, occupied: {cubicle.cubicle_state.__getattribute__("occupied")}, toilet_roll_percentage: {cubicle.cubicle_state.__getattribute__("toilet_roll_percentage")}'
    )
    return CubicleDto(
        id=cubicle.__getattribute__("id"),
        toilet_id=cubicle.__getattribute__("toilet_id"),
        occupied=cubicle.cubicle_state.__getattribute__("occupied"),
        toilet_roll_percentage=cubicle.cubicle_state.__getattribute__(
            "toilet_roll_percentage"
        ),
    )


@router.get("/")
async def get_cubicles(
    mall_id: int, toilet_id: int, cubicles_service: CubiclesService = Depends()
) -> CubiclesListDto:
    cubicles: Sequence[Cubicle] = await cubicles_service.get_cubicles(
        mall_id, toilet_id
    )
    return CubiclesListDto(
        toilet_id=toilet_id,
        cubicles=[
            CubicleDto(
                id=cubicle.__getattribute__("id"),
                toilet_id=cubicle.__getattribute__("toilet_id"),
                occupied=cubicle.cubicle_state.__getattribute__("occupied"),
                toilet_roll_percentage=cubicle.cubicle_state.__getattribute__(
                    "toilet_roll_percentage"
                ),
            )
            for cubicle in cubicles
        ],
    )


@router.put("/{cubicle_id}")
async def update_cubicle(
    mall_id: int,
    toilet_id: int,
    cubicle_id: int,
    cubicle_req_dto: CubicleRequestDto,
    cubicles_service: CubiclesService = Depends(),
) -> CubicleDto:
    cubicle: Cubicle = await cubicles_service.update_cubicle(
        mall_id, toilet_id, cubicle_id, cubicle_req_dto
    )
    return CubicleDto(
        id=cubicle.__getattribute__("id"),
        toilet_id=cubicle.__getattribute__("toilet_id"),
        occupied=cubicle.cubicle_state.__getattribute__("occupied"),
        toilet_roll_percentage=cubicle.cubicle_state.__getattribute__(
            "toilet_roll_percentage"
        ),
    )


@router.delete("/{cubicle_id}")
async def delete_cubicle(
    mall_id: int,
    toilet_id: int,
    cubicle_id: int,
    cubicles_service: CubiclesService = Depends(),
) -> SuccessResponse:
    await cubicles_service.delete_cubicle(mall_id, toilet_id, cubicle_id)
    return SuccessResponse(data="Successfully deleted cubicle.")
