from fastapi import APIRouter
from api.services.populate_service import PopulateService
from fastapi import Depends
from typing import List, Sequence
from db.models import Mall
from db.models import Toilet
from db.models import Cubicle
from db.models import CubicleEvent
from schemas.response_dto.common import SuccessResponse
from schemas.request_dto.populate_request_dto import PopulateRequestDto
from schemas.response_dto.mall_dto import MallDto
from schemas.response_dto.toilet_dto import ToiletDto
from schemas.response_dto.cubicle_dto import CubicleDto
from shared.schemas.state import CubicleEventDto

router = APIRouter(prefix="/populate")


@router.post("/", response_model=SuccessResponse)
async def populate(
    populate_request_dto: PopulateRequestDto,
    populate_service: PopulateService = Depends(),
):
    malls: List[Mall] = await populate_service.populate_malls(
        count=populate_request_dto.mall_count
    )
    toilets: List[Toilet] = await populate_service.populate_toilets(
        mall_ids=[mall.__getattribute__("id") for mall in malls],
        count=populate_request_dto.toilet_count,
    )
    cubicles: List[Cubicle] = await populate_service.populate_cubicles(
        toilet_list=toilets,
        count=populate_request_dto.cubicle_per_toilet,
    )
    events: Sequence[CubicleEvent] = await populate_service.populate_events(
        cubicle_ids=[cubicle.__getattribute__("id") for cubicle in cubicles],
        count=populate_request_dto.event_count,
    )
    return SuccessResponse(
        data={
            "message": "Populate successful",
            "malls": [MallDto.model_validate(mall) for mall in malls],
            "toilets": [ToiletDto.model_validate(toilet) for toilet in toilets],
            "cubicles": [CubicleDto.model_validate(cubicle) for cubicle in cubicles],
            "events": [
                CubicleEventDto(
                    occupied=event.__getattribute__("occupied"),
                    toilet_roll_percentage=event.__getattribute__(
                        "toilet_roll_percentage"
                    ),
                    updated_at=event.__getattribute__("timestamp"),
                )
                for event in events
            ],
        }
    )
