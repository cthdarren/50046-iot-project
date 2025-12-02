from pydantic import BaseModel

class PopulateRequestDto(BaseModel):
    mall_count: int = 4
    toilet_count: int = 6
    cubicle_per_toilet: int = 8
    event_count: int = 15
    mean_minutes: int = 15
    std_minutes: int = 15