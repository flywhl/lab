from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import UUID

from pydantic import Field

from lab.core.model import Model


class InstrumentKind(str, Enum):
    COMPUTE = "compute"  # Generic compute resources
    GPU = "gpu"  # GPU compute resources
    PHYSICAL = "physical"  # Physical lab equipment
    SENSOR = "sensor"  # Measurement devices


class InstrumentStatus(str, Enum):
    AVAILABLE = "available"
    IN_USE = "in_use"
    UNKNOWN = "unknown"


class InstrumentCapability(Model):
    """A specific capability of an instrument"""

    name: str  # e.g. "temperature_measurement", "pressure_control"
    unit: str  # e.g. "celsius", "pascal"
    range: tuple[float, float]  # e.g. (-50, 100)
    precision: float  # e.g. 0.1


class Instrument(Model):
    id: UUID
    kind: InstrumentKind
    capabilities: set[InstrumentCapability]
    status: InstrumentStatus


class InstrumentRequirements(Model):
    """Requirements for instruments needed by an experiment"""

    capabilities: set[InstrumentCapability]


class InstrumentClaim(Model):
    """Active claim on an instrument during execution"""

    instrument: Instrument
    kind: InstrumentKind
    acquired_at: datetime = Field(default_factory=datetime.now)
    released_at: Optional[datetime] = None


class InstrumentMetric(Model):
    """Metrics about instrument state"""

    timestamp: datetime = Field(default_factory=datetime.now)
    instrument: Instrument
    metric_name: str  # e.g. "temperature", "pressure"
    value: float
    unit: Optional[str] = None
