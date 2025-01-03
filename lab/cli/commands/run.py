from pathlib import Path
import logging
import click

from lab.core.logging import setup_logging
from lab.core.ui import UserInterface
from lab.project.service.labfile import LabfileService
from lab.project.service.plan import PlanService
from lab.runtime.persistence.memory import (
    InMemoryExperimentRunRepository,
    InMemoryProjectRunRepository,
)
from lab.runtime.runtime import Runtime
from lab.runtime.service.run import RunService

logger = logging.getLogger("lab")


@click.command()
@click.argument('path', type=click.Path(exists=True, path_type=Path))
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose output')
async def run(path: Path, verbose: bool = False):
    """Run experiments defined in Labfile"""
    # Set up logging and UI
    setup_logging(Path("~/.local/lab/logs/lab.log"))
    ui = UserInterface()

    run_service = RunService(
        project_run_repo=InMemoryProjectRunRepository(),
        experiment_run_repo=InMemoryExperimentRunRepository(),
        subscribers={
            "EXPERIMENT_STARTED": [ui.render_experiment_started],
            "EXPERIMENT_COMPLETED": [ui.render_experiment_completed],
            "EXPERIMENT_FAILED": [ui.render_experiment_failed],
        },
    )
    runtime = Runtime(run_service=run_service)

    try:
        ui.display_start(str(path.resolve()))

        # Load and parse project
        logger.debug("Loading project", extra={"context": {"path": str(path)}})
        labfile_service = LabfileService()
        project = labfile_service.parse(path)

        # Create execution plan
        plan_service = PlanService()
        plan = plan_service.create_execution_plan(project)

        await runtime.start(plan)

        # # Execute experiments with progress display
        # with ui.create_progress() as progress:
        #     task = progress.add_task(
        #         "Running experiments...", total=len(plan.ordered_experiments)
        #     )

        ui.display_success()

    except Exception as e:
        logger.exception("Execution failed")
        ui.display_error(message="Execution failed", details=str(e))
        raise
