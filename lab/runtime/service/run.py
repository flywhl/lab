# src/lab/services/runs.py
from typing import Callable, Mapping, Optional, Sequence, Union
from datetime import datetime
from uuid import UUID

from lab.core.model import Event
from lab.runtime.model.execution import ExecutionContext
from lab.runtime.model.run import (
    ExperimentRun,
    ExperimentRunEvent,
    ProjectRun,
    ProjectRunEvent,
    RunStatus,
)
from lab.runtime.persistence.run import ExperimentRunRepository, ProjectRunRepository


class RunService:
    """Service for managing experiment runs"""

    def __init__(
        self,
        project_run_repo: ProjectRunRepository,
        experiment_run_repo: ExperimentRunRepository,
        subscribers: Mapping[str, Sequence[Callable[[Union[ProjectRunEvent, ExperimentRunEvent]], None]]] | None = None,
    ):
        self._project_run_repo = project_run_repo
        self._experiment_run_repo = experiment_run_repo
        self._subscribers = subscribers or {}

    async def project_run_started(self, run: ProjectRun) -> None:
        """Start tracking a new pipeline run"""
        await self._project_run_repo.save(run)
        await self._emit_event(ProjectRunEvent(run=run, kind="PIPELINE_STARTED"))

    async def experiment_run_started(
        self,
        run: ExperimentRun,
        context: ExecutionContext,
    ) -> ExperimentRun:
        """Start tracking a new experiment run"""
        run.project_run.experiment_runs.append(run)
        # @todo(rory): do we have to save both, or will sqlalchemy do it recursively?
        await self._project_run_repo.save(run.project_run)
        await self._experiment_run_repo.save(run)
        await self._emit_event(ExperimentRunEvent(run=run, kind="EXPERIMENT_STARTED"))
        return run

    async def experiment_run_completed(
        self,
        run: ExperimentRun,
    ) -> None:
        """Mark experiment as completed with results"""
        run.status = RunStatus.COMPLETED
        run.completed_at = datetime.now()
        # run.metrics = metrics
        # run.experiment_data = data
        await self._experiment_run_repo.save(run)
        await self._emit_event(ExperimentRunEvent(run=run, kind="EXPERIMENT_COMPLETED"))

    async def experiment_run_failed(self, run: ExperimentRun, error: str) -> None:
        """Mark experiment as failed"""
        run.status = RunStatus.FAILED
        run.completed_at = datetime.now()
        run.error = error
        await self._experiment_run_repo.save(run)
        await self._emit_event(
            ExperimentRunEvent(run=run, kind="EXPERIMENT_FAILED", data={"error": error})
        )

    async def project_run_failed(self, run: ProjectRun, error: str) -> None:
        """Mark experiment as failed"""
        run.status = RunStatus.FAILED
        run.completed_at = datetime.now()
        run.error = error
        await self._project_run_repo.save(run)
        await self._emit_event(
            ProjectRunEvent(run=run, kind="PROJECT_FAILED", data={"error": error})
        )

    async def project_run_completed(self, project_run: ProjectRun) -> None:
        """Mark pipeline as completed"""
        project_run.status = RunStatus.COMPLETED
        project_run.completed_at = datetime.now()
        await self._project_run_repo.save(project_run)
        await self._emit_event(
            ProjectRunEvent(run=project_run, kind="PROJECT_COMPLETED")
        )

    # Query methods
    async def get_project_run(self, id: UUID) -> Optional[ProjectRun]:
        return await self._project_run_repo.get(id)

    async def get_experiment_run(self, id: UUID) -> Optional[ExperimentRun]:
        return await self._experiment_run_repo.get(id)

    async def list_project_runs(
        self, status: Optional[RunStatus] = None, since: Optional[datetime] = None
    ) -> list[ProjectRun]:
        return await self._project_run_repo.list(status, since)

    async def _emit_event(self, event: Event) -> None:
        """Emit event to subscribers of that event type"""
        subscribers = self._subscribers.get(event.kind, [])
        for subscriber in subscribers:
            try:
                subscriber(event)
            except Exception:
                # Log but don't fail if subscriber errors
                pass
