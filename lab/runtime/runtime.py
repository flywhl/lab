from pathlib import Path
from lab.project.model.plan import ExecutionPlan
from lab.project.model.project import Experiment, Project
from lab.runtime.model.execution import ExecutionContext
from lab.runtime.model.run import (
    ExperimentRun,
    ProjectRun,
    RunStatus,
)
from lab.runtime.service.run import RunService


class Runtime:
    def __init__(self, run_service: RunService):
        self._run_service = run_service

    async def start(self, plan: ExecutionPlan) -> ProjectRun:
        project_run = ProjectRun(status=RunStatus.RUNNING, project=plan.project)
        await self._run_service.project_run_started(project_run)

        try:
            for experiment in plan.ordered_experiments:
                context = await self._create_execution_context(experiment)
                experiment_run = ExperimentRun(
                    experiment=experiment,
                    context=context,
                    status=RunStatus.RUNNING,
                    project_run=project_run,
                )
                await self._run_service.experiment_run_started(experiment_run, context)

                try:
                    await experiment.execution_method.run(context)
                    await self._run_service.experiment_run_completed(experiment_run)
                except Exception as e:
                    await self._run_service.experiment_run_failed(
                        experiment_run, str(e)
                    )

                    # Let orchestrator decide how to handle failure
                    # @todo: design error handling for the runtime...
                    if not self._should_continue(experiment, plan.project, e):
                        break

            await self._run_service.project_run_completed(project_run)
            return project_run
        except Exception as e:
            await self._run_service.project_run_failed(project_run, str(e))
            raise

    def _should_continue(
        self, failed_experiment: Experiment, project: Project, _: Exception
    ) -> bool:
        """
        Determines how to proceed when an experiment fails.
        Returns True if execution should continue, False if it should stop.
        """
        # Get experiments that depend on the failed one
        dependent_experiments = {
            exp for exp in project.experiments if failed_experiment in exp.dependencies
        }

        # If other experiments depend on this one, we should stop
        if dependent_experiments:
            return False

        # If no dependencies, we can continue with other experiments
        return True

    async def _create_execution_context(
        self, experiment: Experiment
    ) -> ExecutionContext:
        # Create context with experiment-specific configuration
        context = ExecutionContext(
            working_dir=Path(f"experiments/{experiment.id}"),
            env_vars={
                "EXPERIMENT_ID": str(experiment.id),
                "EXPERIMENT_NAME": experiment.name,
            },
        )
        return context
