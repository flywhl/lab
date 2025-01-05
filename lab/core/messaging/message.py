# Message type for type hints
from datetime import datetime
from enum import Enum
from typing import TypeVar
import uuid

from pydantic import BaseModel, Field


TMessage = TypeVar("TMessage", bound="Message")


class MessagePriority(str, Enum):
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"


class Message(BaseModel):
    """Base message that all domain messages inherit from"""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = Field(default_factory=datetime.now)
    priority: MessagePriority = MessagePriority.NORMAL

    class Config:
        frozen = True
