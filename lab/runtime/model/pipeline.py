from uuid import UUID, uuid4

from pydantic import Field
from lab.model.model import Model
from lab.model.project import Experiment


class Pipeline(Model):
    id: UUID = Field(default_factory=uuid4)
    experiments: list[Experiment]

    # def run(self):
    #     for exp in self.experiments:
    #
