from datetime import datetime
from typing import Optional, Union
from uuid import UUID

from lab.runtime.model.run import ProjectRun, ExperimentRun, RunStatus
from lab.runtime.persistence.repository import RunRepository

class InMemoryRunRepository(RunRepository):
    """In-memory implementation of RunRepository"""
    
    def __init__(self):
        self._project_runs: dict[UUID, ProjectRun] = {}
        self._experiment_runs: dict[UUID, ExperimentRun] = {}
    
    async def save(self, item: Union[ProjectRun, ExperimentRun]) -> None:
        if isinstance(item, ProjectRun):
            self._project_runs[item.id] = item
        elif isinstance(item, ExperimentRun):
            self._experiment_runs[item.id] = item
        else:
            raise ValueError(f"Unsupported type: {type(item)}")
    
    async def get(self, id: UUID) -> Optional[Union[ProjectRun, ExperimentRun]]:
        return self._project_runs.get(id) or self._experiment_runs.get(id)
    
    async def list(
        self,
        status: Optional[RunStatus] = None,
        since: Optional[datetime] = None,
        **kwargs
    ) -> list[Union[ProjectRun, ExperimentRun]]:
        # Determine which collection to use based on the calling context
        if ProjectRun in self.__class__.__orig_bases__[0].__args__:  # type: ignore
            runs = self._project_runs.values()
        else:
            runs = self._experiment_runs.values()
            
        if status:
            runs = [r for r in runs if r.status == status]
        if since:
            runs = [r for r in runs if r.created_at >= since]
        return list(runs)
