from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path
from typing import Any, Callable

from pydantic import Field

from lab.core.model import Model


class ExecutionMetrics(Model):
    """System-level metrics about the execution"""

    start_time: datetime
    end_time: datetime
    duration_seconds: float
    memory_peak_bytes: int
    cpu_time_seconds: float
    io_read_bytes: int
    io_write_bytes: int


class ExecutionContext(Model):
    """Environment for a single experiment run"""

    working_dir: Path
    env_vars: dict[str, str] = Field(default_factory=dict)
    metrics: list[ExecutionMetrics] = Field(default_factory=list)
    # resource_claims: list[ResourceClaim] = Field(default_factory=list)


class ExecutionMethod(Model, ABC):
    """How an experiment should be executed"""

    # async def prepare(self) -> None: ...
    @abstractmethod
    async def run(self, context: ExecutionContext) -> None: ...

    # async def cleanup(self, cancelled: bool) -> None: ...


class ScriptExecution(ExecutionMethod):
    """Execute a shell command"""

    command: str
    args: list[str]
    env: dict[str, str] = Field(default_factory=dict)

    async def run(self, context: ExecutionContext) -> None:
        print("TODO: implement ScriptExecution.run")


class LocalFunctionExecution(ExecutionMethod):
    """Execute a Python function"""

    func: Callable
    kwargs: dict[str, Any] = Field(default_factory=dict)
    is_async: bool

    async def run(self, context: ExecutionContext) -> None:
        print("TODO: implement LocalFunctionExecution.run")


class APIExecution(ExecutionMethod):
    """Execute via external API (e.g. lab equipment)"""

    endpoint: str
    method: str
    payload: dict[str, Any] = Field(default_factory=dict)

    async def run(self, context: ExecutionContext) -> None:
        print("TODO: implement APIExecution.run")
