from abc import ABC, abstractmethod
from typing import Optional, TypeVar
from pydantic import BaseModel
from uuid import UUID, uuid4

from lab.model.project import Project, Experiment
from labfile.model.tree import LabfileNode


class Definition(BaseModel, ABC):
    """Base class for intermediate definitions"""
    name: str
    
    @abstractmethod
    def to_domain(self, symbols: "SymbolTable") -> Experiment: ...


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


class ExperimentDefinition(Definition):
    """Intermediate representation of an experiment"""
    path: str
    
    def to_domain(self, symbols: SymbolTable) -> Experiment:
        return Experiment(
            id=uuid4(),
            name=self.name,
            path=self.path
        )
