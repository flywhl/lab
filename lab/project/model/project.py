from pathlib import Path
from uuid import UUID
from typing import Any, Callable, Optional, Protocol, TypeAlias, Union

from pydantic import Field

from lab.core.model import Model
from lab.instrument.model.instrument import InstrumentRequirements


ParameterValue: TypeAlias = Union[str, float, int]
Parameters: TypeAlias = dict[str, ParameterValue]


class ExecutionMethod(Protocol):
    """How an experiment should be executed"""

    async def prepare(self) -> None: ...
    async def run(self) -> None: ...
    async def cleanup(self, cancelled: bool) -> None: ...


class ScriptExecution(Model):
    """Execute a shell command"""

    command: str
    args: list[str]
    env: dict[str, str] = Field(default_factory=dict)


class LocalFunctionExecution(Model):
    """Execute a Python function"""

    func: Callable
    kwargs: dict[str, Any] = Field(default_factory=dict)
    is_async: bool


class APIExecution(Model):
    """Execute via external API (e.g. lab equipment)"""

    endpoint: str
    method: str
    payload: dict[str, Any] = Field(default_factory=dict)


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
    experiments: list[Experiment]
