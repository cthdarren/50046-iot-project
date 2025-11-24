from pydantic import BaseModel
    
class MallRequestDto(BaseModel):
    name: str