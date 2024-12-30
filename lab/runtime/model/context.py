from pathlib import Path

from pydantic import Field

from lab.core.model import Model


class ExecutionContext(Model):
    """Environment for a single experiment run"""

    working_dir: Path
    env_vars: dict[str, str] = Field(default_factory=dict)
    # metrics: list[ExecutionMetrics] = Field(default_factory=list)
    # resource_claims: list[ResourceClaim] = Field(default_factory=list)
