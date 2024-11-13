from pathlib import Path
from typing import Annotated
from uuid import uuid4
import rich
import typer
from labfile import parse

from lab.model.project import Experiment, Project
from lab.service.experiment import ExperimentService
from lab.service.labfile import LabfileService
from lab.service.pipeline import PipelineService


def run(path: Annotated[Path, typer.Argument(help="Path to Labfile")]):
    rich.print(f"Running [b]{path.resolve()}[/b]")
    labfile_service = LabfileService()
    project = labfile_service.parse(path)
    print(project)

    experiment_service = ExperimentService()
    pipeline_service = PipelineService(experiment_service=experiment_service)

    pipeline = pipeline_service.create_pipeline(project)
    print(pipeline)


def attach(app: typer.Typer, *, name: str):
    app.command(name=name)(run)
