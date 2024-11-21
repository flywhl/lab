from __future__ import annotations
from types import ModuleType
from typing import TYPE_CHECKING, Callable, Optional, Type

from torch import Tensor

from lab.model.network.dendrites import Dendrite

if TYPE_CHECKING:
    from lab.model.network.population import CellParameters, PopulationState


Namespaces = dict[Type | Callable, ModuleType]
StepFunction = Callable[
    [list[Dendrite], list[Dendrite], "CellParameters", Optional["PopulationState"]],
    "PopulationState",
]
