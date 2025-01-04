import click
from dishka.integrations.click import setup_dishka
from lab.cli.commands.plan import plan

from lab.cli.commands.run import run
from lab.di import DI


def start():
    @click.group()
    @click.pass_context
    def main(context: click.Context):
        di = DI()
        setup_dishka(container=di.container, context=context, auto_inject=True)

    main.command(name="plan")(plan)
    main.command(name="run")(run)

    main()
