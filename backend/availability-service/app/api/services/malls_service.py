from typing import List
from api.repo.malls_repo import MallsRepo
from db.models import Mall
from schemas.response_dto.mall_dto import MallDto


class MallService:
    def __init__(self):
        self.mall_repo = MallsRepo

    def get_mall_by_id(self, id: int) -> Mall | None:
        return None
    
    def get_malls(self) -> List[Mall]:
        return []
