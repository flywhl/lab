from lab.core.messaging.message import Message
from lab.runtime.model.run import ExperimentRun, ProjectRun


class ExperimentRunStarted(Message):
    run: ExperimentRun


class ExperimentRunComplete(Message):
    run: ExperimentRun


class ExperimentRunFailed(Message):
    run: ExperimentRun
    reason: str


class ProjectRunStarted(Message):
    run: ProjectRun


class ProjectRunComplete(Message):
    run: ProjectRun


class ProjectRunFailed(Message):
    run: ProjectRun
    reason: str
