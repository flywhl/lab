from pathlib import Path
import rich
import typer
from labfile import Labfile


def run(labfile: Path):
    rich.print(f"Running [b]{labfile.resolve()}[/b]")
    source = labfile.read_text()
    project = Labfile().parse(source)
    print(project)


def attach(app: typer.Typer, *, name: str):
    app.command(name=name)(run)
