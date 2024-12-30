import rich
from lab.core.service import Service
from lab.project.model.project import Experiment


class ExperimentService(Service):
    def run(self, experiment: Experiment):
        """Run an experiment

        Either
            acquire an instance of the relevant experiment class
            run a script
        """
        rich.print(f"Running [b]{experiment.name}[/b]...")
        rich.print("...done.")

    def dependencies(self): ...
