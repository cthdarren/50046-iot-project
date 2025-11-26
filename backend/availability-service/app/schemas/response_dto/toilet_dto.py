from pydantic import BaseModel, ConfigDict

class ToiletDto(BaseModel):
    id: int
    level: str
    gender: str
    description: str
    mall_id: int

    model_config = ConfigDict(from_attributes=True)