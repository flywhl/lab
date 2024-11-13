from pathlib import Path
from uuid import UUID, uuid4
from typing import Literal, Optional, TypeAlias, Union


from lab.model.model import Model

ParameterValue: TypeAlias = Union[str, float, int]
Parameters: TypeAlias = dict[str, ParameterValue]


class ValueReference(Model):
    owner: "Experiment"
    attribute: str


GPU = Literal["H100"]


class Instrument(Model): ...


# class Dependency(Model): ...


class Compute(Instrument):
    gpu: Optional[GPU]


class Experiment(Model):
    id: UUID
    name: str

    # dependencies: list[Dependency]

    path: Path

    parameters: dict[str, ParameterValue | ValueReference]

    # parameters: Parameters
    # instruments: list[Instrument]

    def __hash__(self) -> int:
        return hash(self.id)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Experiment):
            return NotImplemented
        return self.id == other.id


class Project(Model):
    experiments: list[Experiment]
