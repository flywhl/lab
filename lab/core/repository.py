from abc import ABC, abstractmethod
from typing import Optional, TypeVar, Generic
from uuid import UUID


T = TypeVar("T")


class Repository(ABC, Generic[T]):
    """Abstract base repository"""

    @abstractmethod
    async def save(self, entity: T) -> None: ...

    @abstractmethod
    async def get(self, id: UUID) -> Optional[T]: ...

    @abstractmethod
    async def list(self, **filters) -> list[T]: ...
