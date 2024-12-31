from pathlib import Path
from typing import Annotated
import rich
import typer

from lab.project.service.labfile import LabfileService
from lab.runtime.model.run import ExecutionPlan
from lab.runtime.persistence.run import RunRepository
from lab.runtime.service.run import RunService


def run(path: Annotated[Path, typer.Argument(help="Path to Labfile")]):
    rich.print(f"Running [b]{path.resolve()}[/b]\n")
    labfile_service = LabfileService()
    plan = labfile_service.parse(path)

    db = make_db()
    run_repo = RunRepository(db=db)
    run_service = RunService(repository=run_repo)
    run_service.execute(runtime_plan)


def attach(app: typer.Typer, *, name: str):
    app.command(name=name)(run)
