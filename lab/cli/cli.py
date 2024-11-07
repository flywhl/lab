from typing import Callable, Optional
import typer
import yaml
from lab.model.experiment.experiment import Experiment
from lab.model.spec.network import Spec
from lab.model.util import Vary
from lab.settings import Settings
from tests.model.spec import func

app = typer.Typer()
exp_app = typer.Typer()
app.add_typer(exp_app, name="exp")


# Create sub-apps for each registered experiment
experiment_apps = {}
for name, exp in Experiment.get_registered_experiments().items():
    experiment_apps[name] = typer.Typer()
    exp_app.add_typer(experiment_apps[name], name=name)

    @experiment_apps[name].command("run")
    def run_experiment(
        exp=exp,  # Capture experiment class in closure
        spec: str = typer.Argument(..., help="Specification file name"),
        vary: Optional[str] = typer.Option(None, help="Variation parameter"),
        k: int = typer.Option(1, "--K", "-K", help="Number of iterations"),
    ):
        """Run an experiment with the given specification"""
        vary_ = Vary.parse_str(vary) if vary else None
        spec_class = exp.spec()
        if not spec_class or not issubclass(spec_class, Spec):
            raise typer.BadParameter(f"Experiment {exp} does not have a valid Spec class")

        settings = Settings()
        namespaces = {Callable: func}

        specfile = (
            settings.spec_root / "experiment" / exp.__name__.lower() / f"{spec}.yaml"
        )
        experiment_spec = spec_class.parse_with_namespaces(
            yaml.safe_load(specfile.read_text()), namespaces
        )
        experiment = experiment_spec.build()
        data = experiment(K=k, vary=vary_)
        data.plot()


# @app.command()
# def exp(exp: str, spec: str):
#     """Run a training experiment"""
#     experiments = Experiment.get_registered_experiments()
#     if exp not in experiments:
#         raise ValueError(f"Unknown experiment: {exp}")
#
#     for name, _exp in experiments.items():
#         _exp_app = App(name=name)
#
#     experiment_class = experiments[exp]
#     spec_class = experiment_class.spec()
#     if not spec_class or not issubclass(spec_class, Spec):
#         raise ValueError(f"Experiment {exp} does not have a valid Spec class")
#
#     settings = Settings()
#     namespaces = {Callable: func}
#
#     specfile = (
#         settings.spec_root
#         / "experiment"
#         / experiment_class.__name__.lower()
#         / f"{spec}.yaml"
#     )
#     experiment_spec = spec_class.parse_with_namespaces(
#         yaml.safe_load(specfile.read_text()), namespaces
#     )
#     experiment = experiment_spec.build()
#     experiment.run(hypers=experiment.hypers)
#     # print(f"Experiment {experiment} completed. Result: {result}")


def main():
    app()
