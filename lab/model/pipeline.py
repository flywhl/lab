from lab.model.model import Model
from lab.model.project import Experiment


class Pipeline(Model):
    experiments: list[Experiment]

    # def run(self):
    #     for exp in self.experiments:
    #
