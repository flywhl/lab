# src/lab/services/runs.py
from typing import AsyncIterator, Callable, Optional
from datetime import datetime
from uuid import UUID

from lab.project.model.project import Experiment
from lab.runtime.model.context import ExecutionContext
from lab.runtime.model.execution import ExecutionMetrics
from lab.runtime.persistence.run import RunRepository
from lab.runtime.model.run import (
    ExperimentRun,
    ExperimentRunEvent,
    PipelineRun,
    RunStatus,
)
from lab.runtime.model.pipeline import Pipeline


class RunService:
    """Service for managing experiment runs"""

    def __init__(self, repository: RunRepository):
        self._repository = repository
        self._subscribers: list[Callable[[ExperimentRunEvent], None]] = []

    async def start_pipeline(self, pipeline: Pipeline) -> PipelineRun:
        """Start tracking a new pipeline run"""
        pipeline_run = PipelineRun(
            experiments=pipeline.experiments, status=RunStatus.RUNNING
        )
        await self._repository.save_pipeline_run(pipeline_run)
        await self._emit_event(
            ExperimentRunEvent(run_id=pipeline_run.id, event_type="pipeline_started")
        )
        return pipeline_run

    async def start_experiment(
        self,
        pipeline_run: PipelineRun,
        experiment: Experiment,
        context: ExecutionContext,
    ) -> ExperimentRun:
        """Start tracking a new experiment run"""
        run = ExperimentRun(
            experiment=experiment, context=context, status=RunStatus.RUNNING
        )
        pipeline_run.experiment_runs.append(run)
        await self._repository.save_pipeline_run(pipeline_run)
        await self._emit_event(
            ExperimentRunEvent(run=run, event_type="experiment_started")
        )
        return run

    async def complete_experiment(
        self,
        run: ExperimentRun,
        metrics: list[ExecutionMetrics],
    ) -> None:
        """Mark experiment as completed with results"""
        run.status = RunStatus.COMPLETED
        run.completed_at = datetime.now()
        run.metrics = metrics
        # run.experiment_data = data
        await self._repository.update_experiment_run(run)
        await self._emit_event(
            ExperimentRunEvent(run=run, event_type="experiment_completed")
        )

    async def fail_experiment(self, run: ExperimentRun, error: str) -> None:
        """Mark experiment as failed"""
        run.status = RunStatus.FAILED
        run.completed_at = datetime.now()
        run.error = error
        await self._repository.update_experiment_run(run)
        await self._emit_event(
            ExperimentRunEvent(
                run=run, event_type="experiment_failed", data={"error": error}
            )
        )

    async def complete_pipeline(self, pipeline_run: PipelineRun) -> None:
        """Mark pipeline as completed"""
        pipeline_run.status = RunStatus.COMPLETED
        pipeline_run.completed_at = datetime.now()
        await self._repository.save_pipeline_run(pipeline_run)
        await self._emit_event(
            ExperimentRunEvent(run_id=pipeline_run.id, event_type="pipeline_completed")
        )

    # Query methods
    async def get_pipeline_run(self, id: UUID) -> Optional[PipelineRun]:
        return await self._repository.get_pipeline_run(id)

    async def get_experiment_run(self, id: UUID) -> Optional[ExperimentRun]:
        return await self._repository.get_experiment_run(id)

    async def list_pipeline_runs(
        self, status: Optional[RunStatus] = None, since: Optional[datetime] = None
    ) -> list[PipelineRun]:
        return await self._repository.list_pipeline_runs(status, since)

    # Event handling
    def subscribe(self, callback: Callable[[ExperimentRunEvent], None]) -> None:
        self._subscribers.append(callback)

    async def _emit_event(self, event: ExperimentRunEvent) -> None:
        for subscriber in self._subscribers:
            try:
                subscriber(event)
            except Exception:
                # Log but don't fail if subscriber errors
                pass
