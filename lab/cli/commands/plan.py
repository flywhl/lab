from pathlib import Path
from typing import Annotated
from dishka import FromDishka
import rich
import typer

from lab.core.ui import UserInterface
from lab.project.service.labfile import LabfileService
from lab.project.service.plan import PlanService


def plan(
    path: Annotated[Path, typer.Argument(help="Path to Labfile")],
    ui: FromDishka[UserInterface],
):
    rich.print(f"Generating plan for [b]{path.resolve()}[/b]\n")
    print(ui)
    labfile_service = LabfileService()
    plan_service = PlanService()
    project = labfile_service.parse(path)

    plan = plan_service.create_execution_plan(project)
    print(plan)
