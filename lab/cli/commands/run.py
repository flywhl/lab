from pathlib import Path
import logging
import click
from dishka import FromDishka

from lab.cli.utils import coro
from lab.core.logging import setup_logging
from lab.core.ui import UserInterface
from lab.project.service.labfile import LabfileService
from lab.project.service.plan import PlanService
from lab.runtime.runtime import Runtime

logger = logging.getLogger("lab")


@click.argument("path", type=click.Path(exists=True, path_type=Path))
@coro
async def run(
    path: Path,
    ui: FromDishka[UserInterface],
    runtime: FromDishka[Runtime],
    labfile_service: FromDishka[LabfileService],
    plan_service: FromDishka[PlanService],
):
    """Run experiments defined in Labfile"""
    setup_logging(Path("~/.local/lab/logs/lab.log"))

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
