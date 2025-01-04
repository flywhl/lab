from pathlib import Path
from dishka import FromDishka
import rich
import click

from lab.core.ui import UserInterface
from lab.project.service.labfile import LabfileService
from lab.project.service.plan import PlanService


@click.argument("path", type=click.Path(exists=True, path_type=Path))
def plan(path: Path, ui: FromDishka[UserInterface]):
    """Generate execution plan from Labfile"""
    ui.print(f"Generating plan for [b]{path.resolve()}[/b]\n")
    labfile_service = LabfileService()
    plan_service = PlanService()
    project = labfile_service.parse(path)

    plan = plan_service.create_execution_plan(project)
    ui.print(str(plan))
