from typing import List
from pydantic import BaseModel, ConfigDict
from schemas.response_dto.toilet_dto import ToiletDto

class MallDto(BaseModel):
    id: int
    name: str
    toilets: List[ToiletDto]
    
    model_config = ConfigDict(from_attributes=True)