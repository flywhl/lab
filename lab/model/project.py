from pathlib import Path
from uuid import UUID
from typing import Literal, Optional, TypeAlias, Union


from lab.model.model import Model

ParameterValue: TypeAlias = Union[str, float, int]
Parameters: TypeAlias = dict[str, ParameterValue]


class ValueReference(Model):
    owner: "Experiment"
    attribute: str


GPU = Literal["H100"]


class Instrument(Model): ...


class Compute(Instrument):
    gpu: Optional[GPU]


class Experiment(Model):
    id: UUID
    name: str

    path: Path

    parameters: dict[str, ParameterValue | ValueReference]

    # instruments: list[Instrument]

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
