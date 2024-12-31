from pathlib import Path
from typing import Annotated
import rich
import typer

from lab.project.service.labfile import LabfileService
from lab.project.service.plan import PlanService
from lab.runtime.persistence.memory import (
    InMemoryExperimentRunRepository,
    InMemoryProjectRunRepository,
)
from lab.runtime.runtime import Runtime
from lab.runtime.service.run import RunService


async def run(path: Annotated[Path, typer.Argument(help="Path to Labfile")]):
    rich.print(f"Running [b]{path.resolve()}[/b]\n")
    labfile_service = LabfileService()
    project_run_repo = InMemoryProjectRunRepository()
    experiment_run_repo = InMemoryExperimentRunRepository()
    run_service = RunService(
        project_run_repo=project_run_repo, experiment_run_repo=experiment_run_repo
    )
    runtime = Runtime(run_service=run_service)
    plan_service = PlanService()

    project = labfile_service.parse(path)
    plan = plan_service.create_execution_plan(project)

    await runtime.start(plan)


def attach(app: typer.Typer, *, name: str):
    app.command(name=name)(run)
