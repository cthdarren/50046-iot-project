from pydantic import BaseModel

from schemas.enum.toilet_enum import Gender


class ToiletRequestDto(BaseModel):
    level: str
    gender: Gender
    description: str
    mall_id: int