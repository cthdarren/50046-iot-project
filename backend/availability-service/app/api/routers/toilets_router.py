from typing import List
from fastapi import APIRouter, Depends
from api.services.toilets_service import ToiletsService
from db.models import Toilet
from schemas.request_dto.toilet_request_dto import ToiletRequestDto
from schemas.response_dto.toilet_dto import ToiletDto

router = APIRouter(prefix="/malls/{mall_id}/toilets")


@router.get("/", response_model=List[ToiletDto])
async def get_toilets(
    mall_id: int,
    service: ToiletsService = Depends(),
) -> List[ToiletDto]:
    toilets: List[Toilet] = await service.get_toilets(mall_id)
    return [ToiletDto.model_validate(toilet) for toilet in toilets]


@router.get("/{toilet_id}", response_model=ToiletDto)
async def get_toilet(toilet_id: int, service: ToiletsService = Depends()) -> ToiletDto:
    toilet: Toilet = await service.get_toilet(toilet_id)
    return ToiletDto.model_validate(toilet)


@router.post("/", response_model=ToiletDto)
async def create_toilet(
    req_dto: ToiletRequestDto, service: ToiletsService = Depends()
) -> ToiletDto:
    toilet: Toilet = await service.create_toilet(req_dto)
    return ToiletDto.model_validate(toilet)
