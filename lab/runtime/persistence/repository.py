from abc import ABC, abstractmethod
from datetime import datetime
from typing import Optional, TypeVar, Generic
from uuid import UUID

from lab.runtime.model.run import RunStatus, ProjectRun, ExperimentRun

T = TypeVar('T')

class Repository(ABC, Generic[T]):
    """Abstract base repository"""
    
    @abstractmethod
    async def save(self, item: T) -> None: ...
    
    @abstractmethod
    async def get(self, id: UUID) -> Optional[T]: ...
    
    @abstractmethod
    async def list(self, **filters) -> list[T]: ...

class RunRepository(ABC):
    """Repository interface for run data"""
    
    @abstractmethod
    async def save_project_run(self, run: ProjectRun) -> None: ...
    
    @abstractmethod
    async def save_experiment_run(self, run: ExperimentRun) -> None: ...
    
    @abstractmethod
    async def get_project_run(self, id: UUID) -> Optional[ProjectRun]: ...
    
    @abstractmethod
    async def get_experiment_run(self, id: UUID) -> Optional[ExperimentRun]: ...
    
    @abstractmethod
    async def list_project_runs(
        self, status: Optional[RunStatus] = None, since: Optional[datetime] = None
    ) -> list[ProjectRun]: ...
    
    @abstractmethod
    async def list_experiment_runs(
        self, status: Optional[RunStatus] = None, since: Optional[datetime] = None
    ) -> list[ExperimentRun]: ...
