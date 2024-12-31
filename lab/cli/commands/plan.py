from pathlib import Path
from typing import Annotated
import rich
import typer

from lab.project.service.labfile import LabfileService
from lab.project.service.plan import PlanService


def plan(path: Annotated[Path, typer.Argument(help="Path to Labfile")]):
    rich.print(f"Generating plan for [b]{path.resolve()}[/b]\n")
    labfile_service = LabfileService()
    plan_service = PlanService()
    project = labfile_service.parse(path)

    plan = plan_service.create_execution_plan(project)
    print(plan)


def attach(app: typer.Typer, *, name: str):
    app.command(name=name)(plan)
