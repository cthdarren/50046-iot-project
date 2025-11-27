from pydantic import BaseModel
from typing import List
from .toilet_dto import ToiletDto

class ToiletsListDto(BaseModel):
    mall_id: int
    toilets: List[ToiletDto]