from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional, TypeVar, Union, Any
from labfile.parse.transform import ProcessNode
from pydantic import BaseModel
from uuid import uuid4

from lab.model.project import Project, Experiment, ValueReference
from labfile.model.tree import (
    LabfileNode,
    ReferenceNode,
    ResourceNode,
    LiteralValue as TreeLiteralValue,
)

LiteralValue = Union[int, float, str]


class Definition(BaseModel, ABC):
    """Base class for intermediate definitions"""

    name: str

    @abstractmethod
    def to_domain(self, symbols: "SymbolTable") -> Any: ...


D = TypeVar("D", bound=Definition)


class SymbolTable(BaseModel):
    """Stores intermediate definitions before resolving references"""

    table: dict[str, Definition]

    def lookup(self, key: str, expecting: type[D] = Definition) -> Optional[D]:
        val = self.table.get(key)
        if not val:
            return None

        if not isinstance(val, expecting):
            raise TypeError(
                f"Expected {expecting} but found symbol of type {type(val)}"
            )

        return val


class Reference(BaseModel):
    """A reference to a resource"""

    resource: str
    attribute: str

    @classmethod
    def from_tree(cls, node: ReferenceNode) -> "Reference":
        return cls(resource=node.resource_name, attribute=node.attribute_path)

    @property
    def path(self) -> str:
        return f"{self.resource}.{self.attribute}"


class Parameter(BaseModel):
    """A named parameter with a value"""

    name: str
    value: Union[LiteralValue, Reference]


class ParameterSet(BaseModel):
    """A collection of parameters"""

    values: dict[str, Union[LiteralValue, Reference]]

    @classmethod
    def from_tree(
        cls, parameters: dict[str, Union[TreeLiteralValue, ReferenceNode]]
    ) -> "ParameterSet":
        return cls(
            values={
                k: Reference.from_tree(v) if isinstance(v, ReferenceNode) else v
                for k, v in parameters.items()
            }
        )

    @classmethod
    def from_parameters(cls, parameters: list[Parameter]) -> "ParameterSet":
        return cls(values={param.name: param.value for param in parameters})


class ExperimentDefinition(Definition):
    """Intermediate representation of an experiment"""

    path: str
    parameters: ParameterSet

    @classmethod
    def from_tree(cls, node: ProcessNode) -> "ExperimentDefinition":
        return cls(
            name=node.name,
            path=node.via,
            parameters=ParameterSet.from_tree(node.parameters),
        )

    def to_domain(self, symbols: SymbolTable) -> Experiment:
        parameters = {
            name: self._build_parameter(value, symbols)
            if isinstance(value, Reference)
            else value
            for name, value in self.parameters.values.items()
        }

        return Experiment(
            id=uuid4(), name=self.name, path=Path(self.path), parameters=parameters
        )

    def _build_parameter(self, value: Reference, symbols: SymbolTable):
        ref_name = value.path.split(".")[0]

        # the thing being pointed to
        ref_symbol = symbols.lookup(ref_name, expecting=ExperimentDefinition)
        if not ref_symbol:
            raise ValueError(f"Referenced process {ref_name} not found")

        return ValueReference(owner=ref_symbol.to_domain(symbols), attribute=value.path)
