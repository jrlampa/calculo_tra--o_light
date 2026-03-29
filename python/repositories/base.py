"""Base repository interface for data access layer."""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, List, Optional, Type, TypeVar, Generic
from uuid import UUID

ModelType = TypeVar("ModelType")
CreateSchemaType = TypeVar("CreateSchemaType")
UpdateSchemaType = TypeVar("UpdateSchemaType")


class BaseRepository(Generic[ModelType, CreateSchemaType, UpdateSchemaType], ABC):
    """Abstract base repository for data access operations."""

    def __init__(self, model: Type[ModelType]):
        self.model = model

    @abstractmethod
    async def get(self, id: UUID) -> Optional[ModelType]:
        """Get a single record by ID."""
        pass

    @abstractmethod
    async def get_multi(
        self,
        skip: int = 0,
        limit: int = 100,
        **filters: Any
    ) -> List[ModelType]:
        """Get multiple records with pagination and filters."""
        pass

    @abstractmethod
    async def create(self, obj_in: CreateSchemaType) -> ModelType:
        """Create a new record."""
        pass

    @abstractmethod
    async def update(
        self,
        db_obj: ModelType,
        obj_in: UpdateSchemaType
    ) -> ModelType:
        """Update an existing record."""
        pass

    @abstractmethod
    async def delete(self, id: UUID) -> Optional[ModelType]:
        """Delete a record by ID."""
        pass

    @abstractmethod
    async def count(self, **filters: Any) -> int:
        """Count records with filters."""
        pass
