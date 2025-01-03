import click
from lab.cli.commands.plan import plan
from lab.cli.commands.run import run
from lab.di import DI

@click.group()
def cli():
    """Lab CLI tool for running experiments"""
    di = DI()
    # Setup DI container here if needed
    pass

cli.add_command(plan)
cli.add_command(run)

def main():
    cli()
