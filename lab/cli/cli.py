import typer

from lab.cli.commands import exp, run

app = typer.Typer()


def main():
    exp.attach(app, name="exp")
    run.attach(app, name="run")

    app()
