from datetime import datetime
from enum import Enum
from typing import Any, Optional, Self
from uuid import UUID, uuid4

from pydantic import Field

from lab.core.model import Event, Model
from lab.project.model.project import Experiment, Project
from lab.runtime.model.execution import ExecutionContext


class RunStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ProjectRunEvent(Event):
    """Event emitted during run execution"""

    run: "ProjectRun"


class ExperimentRunEvent(Event):
    """Event emitted during run execution"""

    run: "ExperimentRun"


class ExperimentRun(Model):
    """Instance of a single experiment being executed"""

    id: UUID = Field(default_factory=uuid4)
    experiment: Experiment
    project_run: "ProjectRun"
    context: ExecutionContext
    status: RunStatus = RunStatus.PENDING
    started_at: datetime = Field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    error: Optional[str] = None  # Changed from Exception for serialization
    # metrics: list[ExecutionMetrics] = Field(default_factory=list)
    # instrument_metrics: list[InstrumentMetric] = Field(default_factory=list)


class ExecutionPlan(Model):
    id: UUID = Field(default_factory=uuid4)
    project: Project
    ordered_experiments: list[Experiment]


class ProjectRun(Model):
    """A running instance of a project"""

    id: UUID = Field(default_factory=uuid4)
    project: Project
    experiment_runs: list[ExperimentRun] = Field(default_factory=list)
    status: RunStatus = RunStatus.PENDING
    started_at: datetime = Field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    error: Optional[str] = None  # Changed from Exception for serialization
