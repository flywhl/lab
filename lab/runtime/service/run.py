import logging
from typing import Optional, Union, Mapping
from datetime import datetime
from uuid import UUID

from lab.core.messaging.bus import MessageBus
from lab.core.messaging.message import Message
from lab.runtime.messages import (
    ExperimentRunComplete,
    ExperimentRunFailed,
    ExperimentRunStarted,
    ProjectRunComplete,
    ProjectRunFailed,
    ProjectRunStarted,
)
from lab.runtime.model.execution import ExecutionContext
from lab.runtime.model.run import (
    ExperimentRun,
    ProjectRun,
    RunStatus,
)
from lab.runtime.persistence.run import ExperimentRunRepository, ProjectRunRepository

logger = logging.getLogger(__name__)


class RunService:
    """Service for managing experiment runs"""

    def __init__(
        self,
        project_run_repo: ProjectRunRepository,
        experiment_run_repo: ExperimentRunRepository,
        message_bus: MessageBus,
    ):
        self._project_run_repo = project_run_repo
        self._experiment_run_repo = experiment_run_repo
        self._message_bus = message_bus

    async def project_run_started(self, run: ProjectRun) -> None:
        """Start tracking a new pipeline run"""
        await self._project_run_repo.save(run)
        await self._emit(ProjectRunStarted(run=run))

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
        await self._emit(ExperimentRunStarted(run=run))
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
        await self._emit(ExperimentRunComplete(run=run))

    async def experiment_run_failed(self, run: ExperimentRun, error: str) -> None:
        """Mark experiment as failed"""
        run.status = RunStatus.FAILED
        run.completed_at = datetime.now()
        run.error = error
        await self._experiment_run_repo.save(run)
        await self._emit(ExperimentRunFailed(run=run, reason=error))

    async def project_run_failed(self, run: ProjectRun, error: str) -> None:
        """Mark experiment as failed"""
        run.status = RunStatus.FAILED
        run.completed_at = datetime.now()
        run.error = error
        await self._project_run_repo.save(run)
        await self._emit(ProjectRunFailed(run=run, reason=error))

    async def project_run_completed(self, project_run: ProjectRun) -> None:
        """Mark pipeline as completed"""
        project_run.status = RunStatus.COMPLETED
        project_run.completed_at = datetime.now()
        await self._project_run_repo.save(project_run)
        await self._emit(ProjectRunComplete(run=project_run))

    # Query methods
    async def get_project_run(self, id: UUID) -> Optional[ProjectRun]:
        return await self._project_run_repo.get(id)

    async def get_experiment_run(self, id: UUID) -> Optional[ExperimentRun]:
        return await self._experiment_run_repo.get(id)

    async def list_project_runs(
        self, status: Optional[RunStatus] = None, since: Optional[datetime] = None
    ) -> list[ProjectRun]:
        return await self._project_run_repo.list(status, since)

    async def _emit(self, message: Message) -> None:
        """Emit event to subscribers of that event type"""
        await self._message_bus.publish(message)
