from pydantic import BaseModel, ConfigDict

class CubicleRequestDto(BaseModel):
    toilet_id: int

    model_config = ConfigDict(from_attributes=True)