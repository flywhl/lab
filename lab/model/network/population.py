from __future__ import annotations
from enum import Enum
import inspect
import logging
from typing import TYPE_CHECKING, Annotated, Callable, Iterator, Literal, Self

from pydantic import AfterValidator, Field, ValidationInfo, field_serializer
from torch import Tensor
import torch

from lab.model import Model
from lab.types import StepFunction

if TYPE_CHECKING:
    from lab.model.spec.network import CellParametersSpec


logger = logging.getLogger(__name__)


class Dim(str, Enum):
    B = "B"
    T = "T"
    E = "E"
    N = "N"


B = Dim.B
T = Dim.T
E = Dim.E
N = Dim.N
SIZES = "sizes"


def dimensionality(*sizes: Dim) -> Callable[[Tensor, ValidationInfo], Tensor]:
    assert B in sizes and T in sizes and N in sizes
    assert len(sizes) > 2, f"Must provide at least two dimensions: {sizes}"

    def _validator(
        v: Tensor, info: ValidationInfo, sizes: tuple[Dim, ...] = sizes
    ) -> Tensor:
        min_dim = len(sizes) - 1
        if v.dim() < min_dim:
            v = v.unsqueeze(0)

        return v

    return _validator


class PopulationState(Model):
    """State of a population of neurons

    @note   there must always be a batch dimension, even if it is size 1
    """

    v: Annotated[Tensor, AfterValidator(dimensionality(T, B, E, N))]
    i_syn_local: Annotated[Tensor, AfterValidator(dimensionality(T, B, E, N))]
    i_syn_ff: Annotated[Tensor, AfterValidator(dimensionality(T, B, E, N))]
    i_intrinsic: Annotated[Tensor, AfterValidator(dimensionality(T, B, E, N))]
    spk: Annotated[Tensor, AfterValidator(dimensionality(T, B, E, N))]

    def insert_state(self, other: "PopulationState", at_timestep: int):
        assert (
            self.time is not None
        ), "Cannot insert into a PopulationState that has no time (T) dimension."
        for field in self.model_fields:
            local_val: Tensor | None = getattr(self, field, None)
            assert local_val is not None, f"Field not found in self: {field}"
            other_val: Tensor | None = getattr(other, field, None)
            assert other_val is not None, f"Field not found in other: {field}"

            assert local_val.dim() == other_val.dim(), (
                f"Shape of {field} locally ({local_val.dim()}) must be equal to"
                f" the other ({other_val.dim()})."
            )

        other = other.ensure_time()
        assert other.time is not None
        assert self.time is not None

        if at_timestep >= self.time:
            raise ValueError(
                f"at_timestep ({at_timestep}) must be less than the number of timesteps"
                f" ({self.time})"
            )

        self.v[at_timestep : at_timestep + other.time] = other.v
        self.i_syn_local[at_timestep : at_timestep + other.time] = other.i_syn_local
        self.i_syn_ff[at_timestep : at_timestep + other.time] = other.i_syn_ff
        self.i_intrinsic[at_timestep : at_timestep + other.time] = other.i_intrinsic
        self.spk[at_timestep : at_timestep + other.time] = other.spk

    @property
    def _fields(self) -> Iterator[tuple[str, Tensor, int]]:
        for name, field in self.model_fields.items():
            tensor: Tensor | None = getattr(self, name, None)
            assert tensor is not None, f"Field not found: {field}"
            # Check the length of the default 'size' arg in the validator above
            max_size = len(
                inspect.signature(field.metadata[0].func).parameters[SIZES].default
            )
            yield (name, tensor, max_size)

    def ensure_time(self) -> Self:
        """Ensure that all fields have a time (T) dimension"""
        for name, value, max_size in self._fields:
            if value.dim() == max_size:
                continue
            raise ValueError(
                f"Field {name} has {value.dim()} dimensions, expected {max_size}: {value.shape}"
            )
        return self

    @property
    def batch(self) -> int:
        dims = self.spk.dim()
        if dims == 4:
            return self.spk.shape[1]
        elif dims == 3:
            return self.spk.shape[0]

        raise ValueError(f"Invalid PopulationState shape. spk.shape = {self.spk.dim()}")

    @property
    def time(self) -> int | None:
        dims = self.spk.dim()
        if dims == 4:
            return self.spk.shape[0]
        elif dims == 3:
            return None

        raise ValueError(f"Invalid PopulationState shape. spk.shape = {self.spk.dim()}")

    @classmethod
    def initial(
        cls,
        n_v: int,
        n_syn_local: int,
        n_syn_ff: int,
        n_conductances: int,
        n_units: int,
        kind: Literal["random", "empty"],
        n_time: int = 1,
        n_spk: int = 1,  # TODO: support spikes per-voltage compartment
        n_batch: int = 1,
        **extra,
    ):
        spk_size = (n_batch, n_spk, n_units)
        v_size = (n_batch, n_v, n_units)
        i_syn_local_size = (n_batch, n_syn_local, n_units)
        i_syn_ff_size = (n_batch, n_syn_ff, n_units)
        i_int_size = (n_batch, n_conductances, n_units)

        if n_time is not None:
            spk_size = (n_time, *spk_size)
            v_size = (n_time, *v_size)
            i_syn_local_size = (n_time, *i_syn_local_size)
            i_syn_ff_size = (n_time, *i_syn_ff_size)
            i_int_size = (n_time, *i_int_size)

        _default_empty = dict(
            v=torch.full(v_size, 0.0),
            i_syn_local=torch.full(i_syn_local_size, 0.0),
            i_syn_ff=torch.full(i_syn_ff_size, 0.0),
            i_intrinsic=torch.full(i_int_size, 0.0),
            spk=torch.full(spk_size, 0.0),
        )
        _default_random = dict(
            v=torch.normal(-70.0, 2.0, size=v_size),
            i_syn_local=torch.normal(0.0, 0.01, size=i_syn_local_size),
            i_syn_ff=torch.normal(0.0, 0.01, size=i_syn_ff_size),
            i_intrinsic=torch.normal(0.0, 0.01, size=i_int_size),
            spk=torch.full(spk_size, 0.0),
        )
        _default = _default_random if kind == "random" else _default_empty

        _default.update(extra)

        return cls(**_default)


class Voltage(Model):
    tau: Tensor
    v_leak: Tensor
    v_reset: Tensor
    threshold: Tensor


class Conductance(Model):
    tau: Tensor
    v_eq: Tensor
    a: Tensor  # voltage dependent
    b: Tensor  # effect on voltage


class CellParameters(Model):
    size: int
    dt: float

    voltages: list[Voltage] = Field(..., min_length=1)
    conductances: list[Conductance] = []  # voltage-gated

    step: StepFunction

    activation: str = "spike"

    @classmethod
    def from_spec(
        cls, spec: "CellParametersSpec", step: StepFunction, **_
    ) -> "CellParameters":
        dt = spec.dt.build(float)
        activation = spec.activation.build(str)
        voltages = [v.build() for v in spec.voltages]
        conductances = [c.build() for c in spec.conductances]

        return cls(
            activation=activation,
            size=spec.size,
            dt=dt,
            step=step,
            voltages=voltages,
            conductances=conductances,
        )

    def initial_state(
        self,
        n_batch: int,
        n_syn_local: int,
        n_syn_ff: int,
        n_units: int,
        n_time: int = 1,
        kind: Literal["random", "empty"] = "random",
        **extras,
    ) -> PopulationState:
        return PopulationState.initial(
            n_batch=n_batch,
            n_v=self.num_voltages,
            n_syn_local=n_syn_local,
            n_syn_ff=n_syn_ff,
            n_conductances=self.num_conductances,
            n_units=n_units,
            n_time=n_time,
            kind=kind if self.activation == "spk" else "empty",
            **extras,
        )

    @property
    def num_voltages(self) -> int:
        return len(self.voltages)

    @property
    def num_conductances(self) -> int:
        return len(self.conductances)

    @field_serializer("step")
    def serialize_step_function(self, v: StepFunction, _info):
        return v.__name__
