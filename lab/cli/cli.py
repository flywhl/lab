import typer

from lab.cli.commands import run, plan

app = typer.Typer()


def main():
    plan.attach(app, name="plan")
    run.attach(app, name="run")

    app()
