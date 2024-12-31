from pathlib import Path
from lab.runtime.model.execution import ExecutionContext
from lab.runtime.model.project import Experiment, Project
from lab.runtime.model.run import (
    ExecutionPlan,
    ProjectRun,
)
from lab.runtime.orchestrator import Orchestrator
from lab.runtime.service.run import RunService


class Runtime:
    def __init__(self, run_service: RunService, orchestrator: Orchestrator):
        self._run_service = run_service
        self._orchestrator = orchestrator

    async def start(self, plan: ExecutionPlan) -> ProjectRun:
        project_run = await self._run_service.project_run_started(plan)

        try:
            # Let the orchestrator determine the execution order

            for experiment in plan.ordered_experiments:
                context = await self._create_execution_context(experiment)
                run = await self._run_service.experiment_run_started(
                    project_run, experiment, context
                )

                try:
                    await experiment.execution_method.run(context)
                    await self._run_service.experiment_run_completed(run)
                except Exception as e:
                    await self._run_service.experiment_run_failed(run, str(e))

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
        self, failed_experiment: Experiment, project: Project, error: Exception
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
