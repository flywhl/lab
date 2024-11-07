from typing import Callable, Optional
import typer
import yaml
from lab.model.experiment.experiment import Experiment
from lab.model.spec.network import Spec
from lab.model.util import Vary
from lab.settings import Settings
from tests.model.spec import func

from lab.cli.commands import exp, run

app = typer.Typer()


def main():
    exp.attach(app, name="exp")
    run.attach(app, name="run")

    app()
