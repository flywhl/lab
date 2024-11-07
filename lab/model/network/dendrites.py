from abc import ABC, abstractmethod
import logging
from typing import Callable, Self

from pydantic import Field, field_validator
from torch import Tensor
import torch

from lab.model import Model, Parity

logger = logging.getLogger(__name__)


class Dendrites(ABC, Model):
    """Dendrites"""

    @property
    @abstractmethod
    def all(self) -> list[tuple[str, "Dendrite"]]:
        raise NotImplementedError()


class Dendrite(Model):
    # conditions: list[Callable[[Tensor], Tensor]] = Field(default_factory=list)
    shape: tuple[int, ...]
    tau: float
    parity: Parity = Parity.POS
    signal: Tensor | None = Field(default=None, exclude=True)
    weights: Tensor  # needs shape and an init strategy

    def with_signal(self, signal: Tensor) -> Self:
        self.signal = signal
        return self

    @property
    def current(self) -> Tensor:
        if self.signal is None:
            raise ValueError("No signal!")

        try:
            return self.signal @ (self.weights * self.weights.parity)
            # return (self.signal * self.parity).type(torch.float) @ self.weights
        except Exception as e:
            logger.error(e)
            raise

    def ensure_conditions(self):
        if self.parity:
            self.weights.data.clamp(min=0)
        # for condition in self.conditions:
        #     self.weights.data = condition(self.weights)

    ### Pydantic Stuff

    @field_validator("weights", mode="before")
    @classmethod
    def validate_tensor(cls, v):
        if isinstance(v, list):
            return torch.tensor(v)
        elif isinstance(v, torch.Tensor):
            return v
        else:
            raise ValueError("Must be a torch.Tensor or a list convertible to a tensor")

    # @field_serializer("weights", "signal")
    # def serialize_tensor(self, tensor: Tensor | None, _info):
    #     if tensor is None:
    #         return None
    #     return tensor.tolist()
    # def build(cls, data: dict[str, Any]) -> "Self": ...
