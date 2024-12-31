from lab.cli.commands import run, plan
from lab.cli.utils import AsyncTyper

app = AsyncTyper()


def main():
    plan.attach(app, name="plan")
    run.attach(app, name="run")

    app()
