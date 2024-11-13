from abc import ABC, abstractmethod
from typing import Optional, TypeVar, Union, Any
from pydantic import BaseModel
from uuid import uuid4

from lab.model.project import Project, Experiment
from labfile.model.tree import LabfileNode

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
            raise TypeError(f"Expected {expecting} but found symbol of type {type(val)}")
            
        return val


class Reference(BaseModel):
    """A reference to a resource"""
    resource: str
    attribute: str

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
    def from_parameters(cls, parameters: list[Parameter]) -> "ParameterSet":
        return cls(values={param.name: param.value for param in parameters})


class ExperimentDefinition(Definition):
    """Intermediate representation of an experiment"""
    path: str
    parameters: Optional[ParameterSet] = None
    
    def to_domain(self, symbols: SymbolTable) -> Experiment:
        return Experiment(
            id=uuid4(),
            name=self.name,
            path=self.path
        )
