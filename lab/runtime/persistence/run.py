from abc import abstractmethod
from datetime import datetime
from typing import Optional

from lab.core.repository import Repository
from lab.runtime.model.run import ProjectRun, ExperimentRun, RunStatus


class ProjectRunRepository(Repository[ProjectRun]):
    """Repository interface for project runs"""

    @abstractmethod
    async def list(
        self,
        status: Optional[RunStatus] = None,
        since: Optional[datetime] = None,
        **filters,
    ) -> list[ProjectRun]: ...


class ExperimentRunRepository(Repository[ExperimentRun]):
    """Repository interface for experiment runs"""

    @abstractmethod
    async def list(
        self,
        status: Optional[RunStatus] = None,
        since: Optional[datetime] = None,
        **filters,
    ) -> list[ExperimentRun]: ...
