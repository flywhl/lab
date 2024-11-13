from lab.model.pipeline import Pipeline
from lab.model.project import Experiment


class ExperimentService:
    def run(self, experiment: Experiment):
        """Run an experiment

        Either
            acquire an instance of the relevant experiment class
            run a script
        """
        ...

    def dependencies(self): ...
