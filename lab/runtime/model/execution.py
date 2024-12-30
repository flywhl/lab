from datetime import datetime
from typing import Any, Callable, Protocol

from pydantic import Field

from lab.core.model import Model
from lab.runtime.model.context import ExecutionContext


class ExecutionMetrics(Model):
    """System-level metrics about the execution"""

    start_time: datetime
    end_time: datetime
    duration_seconds: float
    memory_peak_bytes: int
    cpu_time_seconds: float
    io_read_bytes: int
    io_write_bytes: int
