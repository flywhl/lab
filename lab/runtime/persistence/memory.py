from datetime import datetime
from typing import Optional, Dict
from uuid import UUID

from lab.runtime.model.run import ProjectRun, ExperimentRun, RunStatus
from lab.runtime.persistence.run import ProjectRunRepository, ExperimentRunRepository


class InMemoryProjectRunRepository(ProjectRunRepository):
    """In-memory implementation of ProjectRunRepository"""
    
    def __init__(self):
        self._storage: Dict[UUID, ProjectRun] = {}

    async def save(self, entity: ProjectRun) -> ProjectRun:
        self._storage[entity.id] = entity
        return entity

    async def get(self, id: UUID) -> Optional[ProjectRun]:
        return self._storage.get(id)

    async def list(
        self,
        status: Optional[RunStatus] = None,
        since: Optional[datetime] = None,
        **filters
    ) -> list[ProjectRun]:
        results = list(self._storage.values())
        
        if status:
            results = [run for run in results if run.status == status]
            
        if since:
            results = [run for run in results if run.created_at >= since]
            
        return results


class InMemoryExperimentRunRepository(ExperimentRunRepository):
    """In-memory implementation of ExperimentRunRepository"""
    
    def __init__(self):
        self._storage: Dict[UUID, ExperimentRun] = {}

    async def save(self, entity: ExperimentRun) -> ExperimentRun:
        self._storage[entity.id] = entity
        return entity

    async def get(self, id: UUID) -> Optional[ExperimentRun]:
        return self._storage.get(id)

    async def list(
        self,
        status: Optional[RunStatus] = None,
        since: Optional[datetime] = None,
        **filters
    ) -> list[ExperimentRun]:
        results = list(self._storage.values())
        
        if status:
            results = [run for run in results if run.status == status]
            
        if since:
            results = [run for run in results if run.created_at >= since]
            
        return results
