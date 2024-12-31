from datetime import datetime
from typing import Optional
from uuid import UUID

from lab.runtime.model.run import ProjectRun, ExperimentRun, RunStatus
from lab.runtime.persistence.repository import RunRepository

class InMemoryRunRepository(RunRepository):
    """In-memory implementation of RunRepository"""
    
    def __init__(self):
        self._project_runs: dict[UUID, ProjectRun] = {}
        self._experiment_runs: dict[UUID, ExperimentRun] = {}
    
    async def save_project_run(self, run: ProjectRun) -> None:
        self._project_runs[run.id] = run
    
    async def save_experiment_run(self, run: ExperimentRun) -> None:
        self._experiment_runs[run.id] = run
    
    async def get_project_run(self, id: UUID) -> Optional[ProjectRun]:
        return self._project_runs.get(id)
    
    async def get_experiment_run(self, id: UUID) -> Optional[ExperimentRun]:
        return self._experiment_runs.get(id)
    
    async def list_project_runs(
        self, status: Optional[RunStatus] = None, since: Optional[datetime] = None
    ) -> list[ProjectRun]:
        runs = self._project_runs.values()
        if status:
            runs = [r for r in runs if r.status == status]
        if since:
            runs = [r for r in runs if r.created_at >= since]
        return list(runs)
    
    async def list_experiment_runs(
        self, status: Optional[RunStatus] = None, since: Optional[datetime] = None
    ) -> list[ExperimentRun]:
        runs = self._experiment_runs.values()
        if status:
            runs = [r for r in runs if r.status == status]
        if since:
            runs = [r for r in runs if r.created_at >= since]
        return list(runs)
