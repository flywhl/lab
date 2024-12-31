from typing import Any, Callable, Optional, Protocol, TypeAlias
from uuid import UUID

from pydantic import Field
from lab.core.model import Model
from lab.instrument.model.instrument import InstrumentRequirements
from lab.runtime.model.execution import ExecutionMethod


ParameterValue: TypeAlias = str | float | int
Parameters: TypeAlias = dict[str, ParameterValue]


class ValueReference(Model):
    owner: "Experiment"
    attribute: str


class Experiment(Model):
    id: UUID
    name: str

    execution_method: ExecutionMethod

    parameters: dict[str, ParameterValue | ValueReference]
    requirements: Optional[InstrumentRequirements] = None  # TODO(rory)

    def __hash__(self) -> int:
        return hash(self.id)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Experiment):
            return NotImplemented
        return self.id == other.id

    @property
    def dependencies(self) -> set["Experiment"]:
        """Return the set of experiments on which this one depends."""
        return {
            param.owner
            for param in self.parameters.values()
            if isinstance(param, ValueReference) and isinstance(param.owner, Experiment)
        }


class Project(Model):
    experiments: set["Experiment"]
