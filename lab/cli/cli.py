from typing import Callable
from typer import Context, Typer
from lab.cli.commands.plan import plan
from lab.cli.commands.run import run
from lab.cli.commands.test import test
from lab.cli.utils import AsyncTyper, setup_dishka
from lab.di import DI

app = Typer()


def attach(command: Callable, *, to_app: Typer, name: str):
    to_app.command(name=name)(command)


def main():
    di = DI()

    def _dishka(context: Context):
        print("howdy")
        container = di.container
        setup_dishka(container=container, context=context, app=app, auto_inject=True)

    app.callback()(_dishka)

    attach(plan, to_app=app, name="plan")
    attach(run, to_app=app, name="run")
    # attach(test, to_app=app, name=test.__name__)

    app()
