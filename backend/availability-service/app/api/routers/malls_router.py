from typing import List, Union
from fastapi import APIRouter, Depends
from schemas.request_dto.mall_request_dto import MallRequestDto
from db.models import Mall
from schemas.response_dto.mall_dto import MallDto
from schemas.response_dto.common import APIError, ErrorResponse, SuccessResponse
from ..services.malls_service import MallService

router = APIRouter(prefix="/malls")

mall_not_found_error = APIError(code="404", message="No mall found for request.")


@router.get("/", response_model=Union[SuccessResponse, ErrorResponse])
async def get_malls(service: MallService = Depends()) -> SuccessResponse:
    malls: List[Mall] = await service.get_malls()
    return SuccessResponse(data=[MallDto.model_validate(mall) for mall in malls])


@router.get("/{mall_id}", response_model=Union[SuccessResponse, ErrorResponse])
async def get_mall(
    mall_id: int, service: MallService = Depends()
) -> SuccessResponse | ErrorResponse:
    mall = await service.get_mall_by_id(mall_id)
    if mall:
        return SuccessResponse(data=MallDto.model_validate(mall))
    return ErrorResponse(error=mall_not_found_error)


@router.post("/", response_model=Union[SuccessResponse, ErrorResponse])
async def create_mall(
    req_dto: MallRequestDto, service: MallService = Depends()
) -> SuccessResponse | ErrorResponse:
    mall = await service.get_mall_by_name(req_dto.name)
    if mall:
        return ErrorResponse(
            error=APIError(
                code="409", message="A mall with the same name already exists."
            )
        )
    if mall := await service.create_mall(req_dto.name):
        return SuccessResponse(data=MallDto.model_validate(mall))
    return ErrorResponse(
        error=APIError(code="400", message=f"Could not create mall: {req_dto.name}")
    )


@router.put("/{mall_id}", response_model=Union[SuccessResponse, ErrorResponse])
async def update_mall(
    mall_id: int, req_dto: MallRequestDto, service: MallService = Depends()
) -> SuccessResponse | ErrorResponse:
    mall = await service.get_mall_by_id(mall_id)
    if mall:
        updated_mall = await service.update_mall(mall_id, req_dto.name)
        return SuccessResponse(data=MallDto.model_validate(updated_mall))
    return ErrorResponse(error=mall_not_found_error)


@router.delete("/{mall_id}", response_model=Union[SuccessResponse, ErrorResponse])
async def delete_mall(
    mall_id: int, service: MallService = Depends()
) -> SuccessResponse | ErrorResponse:
    mall = await service.get_mall_by_id(mall_id)
    if mall:
        if await service.delete_mall(mall_id):
            return SuccessResponse(data={"message": "Successfully deleted mall."})
        return ErrorResponse(
            error=APIError(code="400", message="Could not delete mall.")
        )
    return ErrorResponse(error=mall_not_found_error)
