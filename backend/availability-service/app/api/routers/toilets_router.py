from typing import Sequence
from fastapi import APIRouter, Depends
from api.services.toilets_service import ToiletsService
from db.models import Toilet
from schemas.request_dto.toilet_request_dto import ToiletRequestDto
from schemas.response_dto.toilet_dto import ToiletDto
from schemas.response_dto.common import SuccessResponse

router = APIRouter(prefix="/malls/{mall_id}/toilets")


@router.get("/", response_model=Sequence[ToiletDto])
async def get_toilets(
    mall_id: int,
    service: ToiletsService = Depends(),
) -> Sequence[ToiletDto]:
    toilets: Sequence[Toilet] = await service.get_toilets(mall_id)
    return [ToiletDto.model_validate(toilet) for toilet in toilets]


@router.get("/{toilet_id}", response_model=ToiletDto)
async def get_toilet(
    mall_id: int, toilet_id: int, service: ToiletsService = Depends()
) -> ToiletDto:
    toilet: Toilet = await service.get_toilet(mall_id, toilet_id)
    return ToiletDto.model_validate(toilet)


@router.post("/", response_model=ToiletDto)
async def create_toilet(
    mall_id: int, req_dto: ToiletRequestDto, service: ToiletsService = Depends()
) -> ToiletDto:
    toilet: Toilet = await service.create_toilet(mall_id, req_dto)
    return ToiletDto.model_validate(toilet)


@router.put("/{toilet_id}", response_model=ToiletDto)
async def update_toilet(
    mall_id: int,
    toilet_id: int,
    req_dto: ToiletRequestDto,
    service: ToiletsService = Depends(),
) -> ToiletDto:
    toilet: Toilet = await service.update_toilet(mall_id, toilet_id, req_dto)
    return ToiletDto.model_validate(toilet)


@router.delete("/{toilet_id}", response_model=SuccessResponse)
async def delete_toilet(
    mall_id: int, toilet_id: int, service: ToiletsService = Depends()
) -> SuccessResponse:
    await service.delete_toilet(mall_id, toilet_id)
    return SuccessResponse(data="Successfully deleted toilet.")
