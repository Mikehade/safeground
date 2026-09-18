"""
Abstract async repository with generic CRUD.
Every concrete repo inherits from this — DI-friendly, testable.
"""
from abc import ABC
from typing import Any, Dict, Generic, List, Optional, Type, TypeVar
from uuid import UUID

from sqlalchemy import and_, delete, select, update
from infrastructure.db.base import Base

ModelType = TypeVar("ModelType", bound=Base)


class BaseRepository(ABC, Generic[ModelType]):

    def __init__(self, model: Type[ModelType], session_factory):
        self.model = model
        self.session_factory = session_factory

    async def get_by_id(self, id: UUID) -> Optional[ModelType]:
        async with self.session_factory() as session:
            result = await session.execute(
                select(self.model).where(self.model.id == id)
            )
            return result.scalars().first()

    async def get_all(
        self,
        skip: int = 0,
        limit: int = 100,
        filters: Optional[List] = None,
    ) -> List[ModelType]:
        async with self.session_factory() as session:
            query = select(self.model)
            if filters:
                query = query.where(and_(*filters))
            query = query.offset(skip).limit(limit)
            result = await session.execute(query)
            return list(result.scalars().all())

    async def create(self, obj_in: Dict[str, Any]) -> ModelType:
        async with self.session_factory() as session:
            db_obj = self.model(**obj_in)
            session.add(db_obj)
            await session.flush()
            await session.refresh(db_obj)
            return db_obj

    async def update_by_id(
        self, id: UUID, obj_in: Dict[str, Any]
    ) -> Optional[ModelType]:
        async with self.session_factory() as session:
            await session.execute(
                update(self.model)
                .where(self.model.id == id)
                .values(**obj_in)
            )
        return await self.get_by_id(id)

    async def delete_by_id(self, id: UUID) -> bool:
        async with self.session_factory() as session:
            result = await session.execute(
                delete(self.model).where(self.model.id == id)
            )
            return result.rowcount > 0
