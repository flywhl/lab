from datetime import datetime
from typing import Optional
from uuid import UUID

from sqlalchemy import Engine

from lab.runtime.model.run import ExperimentRun, ProjectRun, RunStatus
from lab.runtime.persistence.repository import RunRepository


class SQLRunRepository(RunRepository):
    """SQLAlchemy implementation of RunRepository"""

    def __init__(self, db: Engine):
        self._db = db

    async def save_project_run(self, run: ProjectRun) -> None: ...
    async def save_experiment_run(self, run: ExperimentRun) -> None: ...
    async def get_project_run(self, id: UUID) -> Optional[ProjectRun]: ...
    async def get_experiment_run(self, id: UUID) -> Optional[ExperimentRun]: ...
    async def list_project_runs(
        self, status: Optional[RunStatus] = None, since: Optional[datetime] = None
    ) -> list[ProjectRun]: ...
    async def list_experiment_runs(
        self, status: Optional[RunStatus] = None, since: Optional[datetime] = None
    ) -> list[ExperimentRun]: ...
