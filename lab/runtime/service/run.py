# src/lab/services/runs.py
from typing import Callable, Optional
from datetime import datetime
from uuid import UUID

from lab.core.model import Event
from lab.project.model.project import Experiment
from lab.runtime.model.execution import ExecutionContext
from lab.runtime.persistence.run import RunRepository
from lab.runtime.model.run import (
    ExecutionPlan,
    ExperimentRun,
    ExperimentRunEvent,
    ProjectRun,
    ProjectRunEvent,
    RunStatus,
)


class RunService:
    """Service for managing experiment runs"""

    def __init__(self, repository: RunRepository):
        self._repository = repository
        self._subscribers: list[Callable[[Event], None]] = []

    async def execute(self, plan: ExecutionPlan): ...

    async def project_run_started(self, plan: ExecutionPlan) -> ProjectRun:
        """Start tracking a new pipeline run"""
        project_run = ProjectRun(status=RunStatus.RUNNING, project=plan.project)
        await self._repository.save_project_run(project_run)
        await self._emit_event(
            ProjectRunEvent(run=project_run, kind="PIPELINE_STARTED")
        )
        return project_run

    async def experiment_run_started(
        self,
        project_run: ProjectRun,
        experiment: Experiment,
        context: ExecutionContext,
    ) -> ExperimentRun:
        """Start tracking a new experiment run"""
        run = ExperimentRun(
            experiment=experiment,
            context=context,
            status=RunStatus.RUNNING,
            project_run=project_run,
        )
        project_run.experiment_runs.append(run)
        await self._repository.save_project_run(project_run)
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
        await self._repository.save_experiment_run(run)
        await self._emit_event(ExperimentRunEvent(run=run, kind="EXPERIMENT_COMPLETED"))

    async def experiment_run_failed(self, run: ExperimentRun, error: str) -> None:
        """Mark experiment as failed"""
        run.status = RunStatus.FAILED
        run.completed_at = datetime.now()
        run.error = error
        await self._repository.save_experiment_run(run)
        await self._emit_event(
            ExperimentRunEvent(run=run, kind="EXPERIMENT_FAILED", data={"error": error})
        )

    async def project_run_failed(self, run: ProjectRun, error: str) -> None:
        """Mark experiment as failed"""
        run.status = RunStatus.FAILED
        run.completed_at = datetime.now()
        run.error = error
        await self._repository.save_project_run(run)
        await self._emit_event(
            ProjectRunEvent(run=run, kind="PROJECT_FAILED", data={"error": error})
        )

    async def project_run_completed(self, project_run: ProjectRun) -> None:
        """Mark pipeline as completed"""
        project_run.status = RunStatus.COMPLETED
        project_run.completed_at = datetime.now()
        await self._repository.save_project_run(project_run)
        await self._emit_event(
            ProjectRunEvent(run=project_run, kind="PROJECT_COMPLETED")
        )

    # Query methods
    async def get_project_run(self, id: UUID) -> Optional[ProjectRun]:
        return await self._repository.get_project_run(id)

    async def get_experiment_run(self, id: UUID) -> Optional[ExperimentRun]:
        return await self._repository.get_experiment_run(id)

    async def list_project_runs(
        self, status: Optional[RunStatus] = None, since: Optional[datetime] = None
    ) -> list[ProjectRun]:
        return await self._repository.list_project_runs(status, since)

    # Event handling
    def subscribe(self, callback: Callable[[Event], None]) -> None:
        self._subscribers.append(callback)

    async def _emit_event(self, event: Event) -> None:
        for subscriber in self._subscribers:
            try:
                subscriber(event)
            except Exception:
                # Log but don't fail if subscriber errors
                pass
