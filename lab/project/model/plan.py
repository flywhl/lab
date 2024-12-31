from uuid import UUID, uuid4

from pydantic import Field
from lab.core.model import Model
from lab.project.model.project import Experiment, Project


class ExecutionPlan(Model):
    id: UUID = Field(default_factory=uuid4)
    project: Project
    ordered_experiments: list[Experiment]
