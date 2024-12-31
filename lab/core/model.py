from datetime import datetime
from typing import Any
from pydantic import BaseModel, ConfigDict, Field


class Model(BaseModel):
    model_config = ConfigDict(frozen=True)


class Event(Model):
    timestamp: datetime = Field(default_factory=datetime.now)
    kind: str
    data: dict[str, Any] = Field(default_factory=dict)
