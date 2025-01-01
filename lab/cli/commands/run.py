from pathlib import Path
from typing import Annotated, Optional
import logging
import typer

from lab.core.logging import setup_logging
from lab.core.ui import UserInterface
from lab.project.service.labfile import LabfileService
from lab.project.service.plan import PlanService
from lab.runtime.model.run import ExperimentRunEvent
from lab.runtime.persistence.memory import (
    InMemoryExperimentRunRepository,
    InMemoryProjectRunRepository,
)
from lab.runtime.runtime import Runtime
from lab.runtime.service.run import RunService

logger = logging.getLogger("lab")


async def run(
    path: Annotated[Path, typer.Argument(help="Path to Labfile")],
    verbose: Annotated[bool, typer.Option("--verbose", "-v")] = False,
    log_file: Annotated[
        Optional[Path], typer.Option("--log-file", help="Write logs to file")
    ] = Path.home() / ".local" / "lab" / "logs" / "lab.log",
):
    """Run experiments defined in Labfile"""
    # Set up logging and UI
    setup_logging(log_file)
    ui = UserInterface(verbose=verbose)

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

        # Execute experiments with progress display
        with ui.create_progress() as progress:
            task = progress.add_task(
                "Running experiments...", total=len(plan.ordered_experiments)
            )
            results = await runtime.start(plan)

        # Show results

    except Exception as e:
        logger.exception("Execution failed")
        ui.display_error(message="Execution failed", details=str(e))
        raise


def attach(app: typer.Typer, *, name: str):
    app.command(name=name)(run)
