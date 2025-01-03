from datetime import datetime
from typing import Any, Generic, Protocol, TypeVar
from pydantic import BaseModel, Field


class Model(BaseModel): ...


class Event(Model):
    timestamp: datetime = Field(default_factory=datetime.now)
    kind: str
    data: dict[str, Any] = Field(default_factory=dict)


E = TypeVar("E", bound=Event, contravariant=True)


class EventHandler(Protocol, Generic[E]):
    def __call__(self, event: E) -> None: ...
