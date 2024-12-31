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

class ProjectRunRepository(Repository[ProjectRun]):
    """Repository interface for project runs"""
    
    @abstractmethod
    async def list(
        self, 
        status: Optional[RunStatus] = None, 
        since: Optional[datetime] = None
    ) -> list[ProjectRun]: ...

class ExperimentRunRepository(Repository[ExperimentRun]):
    """Repository interface for experiment runs"""
    
    @abstractmethod
    async def list(
        self,
        status: Optional[RunStatus] = None,
        since: Optional[datetime] = None
    ) -> list[ExperimentRun]: ...

class RunRepository(ProjectRunRepository, ExperimentRunRepository):
    """Combined repository interface for both project and experiment runs"""
    
    async def save_project_run(self, run: ProjectRun) -> None:
        await self.save(run)
        
    async def save_experiment_run(self, run: ExperimentRun) -> None:
        await self.save(run)
        
    async def get_project_run(self, id: UUID) -> Optional[ProjectRun]:
        return await self.get(id)
        
    async def get_experiment_run(self, id: UUID) -> Optional[ExperimentRun]:
        return await self.get(id)
        
    async def list_project_runs(
        self,
        status: Optional[RunStatus] = None,
        since: Optional[datetime] = None
    ) -> list[ProjectRun]:
        return await self.list(status=status, since=since)
        
    async def list_experiment_runs(
        self,
        status: Optional[RunStatus] = None,
        since: Optional[datetime] = None
    ) -> list[ExperimentRun]:
        return await self.list(status=status, since=since)
