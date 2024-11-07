from typing import Callable, Optional
from cyclopts import App
import yaml
from lab.model.experiment.experiment import Experiment

from lab.model.spec.network import Spec


from lab.model.util import Vary
from lab.settings import Settings
from tests.model.spec import func

lab = App(name="lab")
exp_parent_app = App(name="exp")

lab.command(exp_parent_app)


for name, exp in Experiment.get_registered_experiments().items():
    exp_app = App(name=name)
    exp_parent_app.command(exp_app)

    @exp_app.command()
    def run(spec: str, vary: Optional[str] = None, K: int = 1):
        vary_ = Vary.parse_str(vary) if vary else None
        spec_class = exp.spec()
        if not spec_class or not issubclass(spec_class, Spec):
            raise ValueError(f"Experiment {exp} does not have a valid Spec class")

        settings = Settings()
        namespaces = {Callable: func}

        specfile = (
            settings.spec_root / "experiment" / exp.__name__.lower() / f"{spec}.yaml"
        )
        experiment_spec = spec_class.parse_with_namespaces(
            yaml.safe_load(specfile.read_text()), namespaces
        )
        experiment = experiment_spec.build()
        data = experiment(K=K, vary=vary_)
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
    lab()
