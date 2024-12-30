from datetime import datetime
from typing import Optional
from uuid import UUID
from lab.model.run import ExperimentRun, PipelineRun, RunStatus


class RunRepository:
    """Persistent storage for run data"""

    def __init__(self, db: Database):  # Some DB abstraction
        self._db = db

    async def save_pipeline_run(self, run: PipelineRun) -> None: ...
    async def update_experiment_run(self, run: ExperimentRun) -> None: ...
    async def get_pipeline_run(self, id: UUID) -> Optional[PipelineRun]: ...
    async def get_experiment_run(self, id: UUID) -> Optional[ExperimentRun]: ...
    async def list_pipeline_runs(
        self, status: Optional[RunStatus] = None, since: Optional[datetime] = None
    ) -> list[PipelineRun]: ...
    async def list_experiment_runs(
        self, status: Optional[RunStatus] = None, since: Optional[datetime] = None
    ) -> list[PipelineRun]: ...
