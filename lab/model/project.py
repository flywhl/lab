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


class Project(Model):
    experiments: list[Experiment]
