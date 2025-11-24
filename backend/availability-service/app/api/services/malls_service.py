from typing import List
from api.repo.malls_repo import MallsRepo
from db.models import Mall

class MallService:
    def __init__(self) -> None:
        self.mall_repo = MallsRepo

    async def get_mall_by_id(self, id: int) -> Mall | None:
        return None
    
    async def get_mall_by_name(self, name: str) -> Mall | None:
        return None
    
    async def get_malls(self) -> List[Mall]:
        return []
    
    async def create_mall(self, name: str) -> Mall | None:
        return Mall(id=1, name=name, toilets=[])

    async def update_mall(self, mall_id: int, name: str) -> Mall | None:
        return Mall()
    
    async def delete_mall(self, mall_id: int) -> bool:
        return False