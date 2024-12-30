from lab.project.model.project import Project
from lab.runtime.model.context import ExecutionContext
from lab.runtime.model.pipeline import Pipeline
from lab.runtime.model.run import PipelineRun
from lab.runtime.orchestrator import Orchestrator
from lab.runtime.service.run import RunService


class Runtime:
    def __init__(self, run_service: RunService, orchestrator: Orchestrator):
        self._run_service = run_service
        self._orchestrator = orchestrator

    async def start(self, project: Project) -> PipelineRun:
        # Create a pipeline run to track the overall execution
        pipeline_run = await self._run_service.start_pipeline(project)

        try:
            # Let the orchestrator determine the execution order
            execution_order = await self._orchestrator.resolve_execution_order(project)

            for experiment in execution_order:
                context = await self._create_execution_context(experiment)
                run = await self._run_service.start_experiment(
                    pipeline_run, experiment, context
                )

                try:
                    await experiment.execution_method.run(context)
                    await self._run_service.complete_experiment(run, context)
                except Exception as e:
                    await self._run_service.fail_experiment(run, str(e))
                    # Let orchestrator decide how to handle failure
                    if not await self._orchestrator.handle_failure(
                        project, experiment, e
                    ):
                        break

            await self._run_service.complete_pipeline(pipeline_run)
            return pipeline_run
        except Exception as e:
            await self._run_service.fail_pipeline(pipeline_run, str(e))
            raise

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
