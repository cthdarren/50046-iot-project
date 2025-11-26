from schemas.request_dto.toilet_request_dto import ToiletRequestDto
from sqlalchemy import select, delete
from db.models import Toilet
from typing import Optional, Sequence


class ToiletsRepo:
    def __init__(self, db):
        self.db = db

    async def create_toilet(self, mall_id: int, req_dto: ToiletRequestDto):
        new_toilet: Toilet = Toilet(
            level=req_dto.level,
            gender=req_dto.gender.value,
            description=req_dto.description,
            mall_id=mall_id,
        )
        self.db.add(new_toilet)
        await self.db.flush()
        await self.db.commit()
        await self.db.refresh(new_toilet)
        return new_toilet

    async def get_toilets(self, mall_id: int):
        statement = select(Toilet).where(Toilet.mall_id == mall_id)
        result = await self.db.execute(statement)
        return result.scalars().all()

    async def get_toilet(self, toilet_id: int, mall_id: int):
        statement = select(Toilet).where(Toilet.id == toilet_id, Toilet.mall_id == mall_id)
        result = await self.db.execute(statement)
        return result.scalar_one_or_none()
    async def get_toilets_by_fields(self, mall_id: int, gender: Optional[str] = None, level: Optional[str] = None, description: Optional[str] = None) -> Sequence[Toilet]:
        statement = select(Toilet).where(Toilet.mall_id == mall_id)
        if gender:
            statement = statement.where(Toilet.gender == gender)
        if level:
            statement = statement.where(Toilet.level == level)
        if description:
            statement = statement.where(Toilet.description == description)
        result = await self.db.execute(statement)
        return result.scalars().all()

    async def update_toilet(self, toilet: Toilet, req_dto: ToiletRequestDto):
        model_dict = req_dto.model_dump(exclude_unset=True)
        if "gender" in model_dict:
            model_dict["gender"] = model_dict["gender"].value
        for k, v in model_dict.items():
            setattr(toilet, k, v)
        await self.db.commit()
        await self.db.refresh(toilet)
        return toilet

    async def delete_toilet(self, toilet_id: int, mall_id: int):
        statement = delete(Toilet).where(Toilet.id == toilet_id, Toilet.mall_id == mall_id)
        await self.db.execute(statement)
        await self.db.commit()
        return True
