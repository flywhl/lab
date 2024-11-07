from abc import ABC
from enum import Enum
from pathlib import Path
from typing import (
    Any,
    Callable,
    ClassVar,
    Generic,
    Optional,
    Self,
    Type,
    TypeVar,
)
from pydantic import Field, ValidationInfo, field_validator, model_validator
from torch import Tensor
import torch
from torch.optim.adam import Adam
from torch.optim.optimizer import Optimizer
from torch.nn.parameter import Parameter

from lab.model.dataset.dataset import Dataset
from lab.model.network.dendrites import Dendrite
from lab.model.network.population import CellParameters, Conductance, Voltage
from lab.model.network.layer import Layer
from lab.model.network.network import Network
from lab.settings import Settings
from lab.model import Model
from lab.types import Namespaces

T = TypeVar("T")


class Spec(Model, Generic[T]):
    _namespaces: ClassVar[Namespaces] = {}

    @classmethod
    def set_namespaces(cls, namespaces: Namespaces):
        cls._namespaces = namespaces

    @classmethod
    def parse_with_namespaces(cls, data: dict, namespaces: Namespaces) -> "Self":
        cls.set_namespaces(namespaces)
        instance = cls.model_validate(data)
        instance._propagate_namespaces()
        return instance

    def _propagate_namespaces(self) -> None:
        for field_name, _ in self.model_fields.items():
            field_value = getattr(self, field_name)
            if isinstance(field_value, Spec):
                field_value.__class__.set_namespaces(self._namespaces)
                field_value._propagate_namespaces()
            elif isinstance(field_value, list):
                for item in field_value:
                    if isinstance(item, Spec):
                        item.__class__.set_namespaces(self._namespaces)
                        item._propagate_namespaces()
            elif isinstance(field_value, dict):
                for item in field_value.values():
                    if isinstance(item, Spec):
                        item.__class__.set_namespaces(self._namespaces)
                        item._propagate_namespaces()

    @model_validator(mode="after")
    def propagate_namespaces(self) -> "Self":
        self._propagate_namespaces()
        return self

    # @abstractmethod
    def build(self, *_, **__) -> T:
        raise NotImplementedError()


### Network

GaussianInitialisation = tuple[float, float]
CriticalInitialisation = float

V = TypeVar("V", float, str, Tensor)


class ValueSpec(Spec[V]):
    val: float | str

    def build(self, as_type: Optional[Type[V]] = None, *_, **__) -> V:
        assert as_type is not None
        if issubclass(as_type, Tensor):
            if not isinstance(self.val, float):
                raise ValueError(f"Tried to build a Tensor from a {type(self.val)}.")
            return as_type(1).fill_(self.val)
        elif issubclass(as_type, float):
            if isinstance(self.val, float):
                return as_type(self.val)
            raise ValueError(f"Expected a float: {self.val}")
        elif issubclass(as_type, str):
            if isinstance(self.val, str):
                return as_type(self.val)

        raise ValueError(f"Cannot build ValueSpec: {self}")


class InitSpec(ABC, Spec[T], Generic[T]):
    train: bool = False
    init: GaussianInitialisation
    min: Optional[float] = None
    max: Optional[float] = None


class PopulationParameterSpec(InitSpec[Tensor]):
    def build(self, *_, **__) -> Tensor:
        raise NotImplementedError()


class Dale(Enum):
    INH = -1
    EXC = 1


class DendriteSpec(InitSpec[Dendrite]):
    shape: tuple[int, int]
    tau: float
    density: float | None = None
    dale: Dale | None = None

    def build(self, *_, **__) -> Dendrite:
        weights = torch.normal(mean=self.init[0], std=self.init[1], size=self.shape)
        weights = Parameter(weights, requires_grad=True)
        conditions: list[Callable[[Tensor], Tensor]] = []
        if self.density:
            density_mask = (
                torch.rand(weights.shape, requires_grad=False, device=None)
                < self.density
            ).float()
            weights.data *= density_mask
            weights.register_hook(lambda grad: grad * density_mask)

        if self.dale:
            weights.data = weights.data.abs()

            conditions.append(lambda w: w.data.clamp(0))

        return Dendrite(weights=weights, tau=self.tau, conditions=conditions)


class VoltageSpec(Spec[Voltage]):
    tau: PopulationParameterSpec | ValueSpec[Tensor]
    v_leak: PopulationParameterSpec | ValueSpec[Tensor]
    v_reset: PopulationParameterSpec | ValueSpec[Tensor]
    threshold: PopulationParameterSpec | ValueSpec[Tensor]

    def build(self, *_, **__) -> Voltage:
        return Voltage(
            tau=self.tau.build(Tensor),
            v_leak=self.v_leak.build(Tensor),
            v_reset=self.v_reset.build(Tensor),
            threshold=self.threshold.build(Tensor),
        )

    @field_validator("*", mode="before")
    @classmethod
    def parse_values(cls, v: Any, info: ValidationInfo):
        if isinstance(v, dict):
            return v
        if isinstance(v, (int, float)):
            return ValueSpec[Tensor](val=v)

        raise ValueError(
            f"Unexpected value for {info.field_name}: {v}\t(type: {type(v)})"
        )


class ConductanceSpec(Spec[Conductance]):
    tau: PopulationParameterSpec | ValueSpec[Tensor]
    v_eq: PopulationParameterSpec | ValueSpec[Tensor]
    a: PopulationParameterSpec | ValueSpec[Tensor]
    b: PopulationParameterSpec | ValueSpec[Tensor]

    def build(self, *_, **__) -> Conductance:
        return Conductance(
            tau=self.tau.build(Tensor),
            v_eq=self.v_eq.build(Tensor),
            a=self.a.build(Tensor),
            b=self.b.build(Tensor),
        )

    @field_validator("*", mode="before")
    @classmethod
    def parse_values(cls, v: Any, info: ValidationInfo):
        if isinstance(v, dict):
            return v
        if isinstance(v, (int, float)):
            return ValueSpec[Tensor](val=v)

        raise ValueError(
            f"Unexpected value for {info.field_name}: {v}\t(type: {type(v)})"
        )


class CellParametersSpec(Spec[CellParameters]):
    preset: str
    step: str
    size: int
    voltages: list[VoltageSpec] = Field(min_length=1, max_length=1)
    conductances: list[ConductanceSpec] = Field(default_factory=list)
    activation: ValueSpec[str]
    dt: ValueSpec[float]

    def build(self, *_, **__) -> CellParameters:
        type_ = Callable
        namespace = self._namespaces.get(type_, None)

        if not namespace:
            raise ValueError(f"Namespace not found for {type_}")

        step = getattr(namespace, self.step, None)
        if not step:
            raise ValueError(
                f"Step function {self.step} not found in namespace {type_}"
            )

        return CellParameters.from_spec(self, step=step)

    # TODO: use @field_validator("*", mode="before") instead?
    @field_validator("activation", "dt", mode="before")
    @classmethod
    def parse_values(cls, v: Any, info: ValidationInfo):
        if isinstance(v, float):
            return ValueSpec[float](val=v)
        if isinstance(v, str):
            return ValueSpec[str](val=v)

        raise ValueError(
            f"Unexpected value for {info.field_name}: {v}\t(type: {type(v)})"
        )


class LayerSpec(Spec[Layer]):
    populations: dict[str, CellParametersSpec]
    ff_dendrites: dict[str, dict[str, DendriteSpec]]
    local_dendrites: dict[str, dict[str, DendriteSpec]] = Field(default_factory=dict)

    def build(self, **_) -> Layer:
        return Layer.from_spec(self)

    # @classmethod
    # def klass_from(cls, kind: str) -> Type:
    #     type_ = Layer  # TODO: do not hard code
    #     namespace = cls._namespaces.get(type_, None)
    #     if not namespace:
    #         raise ValueError(f"No namespace for {type_}")
    #
    #     klass = getattr(namespace, kind, None)
    #
    #     if not klass:
    #         raise ValueError(f"Class not found in {type_} namespace: {kind}")
    #
    #     return klass


class NetworkSpec(Spec[Network]):
    # shape: list[int | dict[str, int]]
    layers: list[LayerSpec]

    def build(self, **_) -> Network:
        # assert len(self.shape) > 1 and isinstance(
        #     self.shape[0], int
        # ), "You must specify the input size as the first of the layer shapes."
        layers = [
            layer.build()  # prev_shape=self.shape[i - 1], self_shape=self.shape[i])
            for layer in self.layers
            # for i, layer in enumerate(self.layers, start=1)
        ]
        return Network(layers=layers)


### Training


class OptimizerSpec(Spec[Optimizer]):
    cls: str
    args: dict[str, Any]

    def build(self, *, params: dict[str, Tensor], **_) -> Optimizer:
        return Adam(params=params.values())


class DatasetSpec(Spec[Dataset]):
    path: Path
    load_fn: str

    def build(self, *_, **__) -> Dataset:
        type_ = Callable
        namespace = self._namespaces.get(type_, None)

        if not namespace:
            raise ValueError(f"Namespace not found for {type_}")

        load = getattr(namespace, self.load_fn, None)
        if not load:
            raise ValueError(f"Function {self.load_fn} not found in namespace {type_}")

        settings = Settings()
        return Dataset(loc=settings.root / self.path, load_data=load)


### Experiment


# class ExperimentSpec(Spec[T], Generic[T]):
#
#     @classmethod
#     @abstractmethod
#     def load(
#         cls, spec: str, namespaces: Namespaces, settings: Settings
#     ) -> "ExperimentSpec[T]":
#         raise NotImplementedError()


# assert not isinstance(self.value, str)
# val = self.value * self.scale
# if self.std is not None:
#     std = self.std * self.scale
#     if self.count > 1:
#         size = (self.count, N)
#     else:
#         size = (N,)
#     tensor = torch.normal(mean=val, std=std, size=size, device=DEVICE)
# else:
#     tensor = torch.as_tensor(val, device=DEVICE)
#
# if self.abs:
#     tensor = torch.abs(tensor)
#
# if self.round:
#     tensor = tensor.int()
#
# if self.minimum is not None:
#     tensor[tensor < self.minimum] = self.minimum
#
# if self.maximum is not None:
#     tensor[tensor > self.maximum] = self.maximum
#
# if self.train:
#     param = Parameter(tensor, requires_grad=True)
#
#     return param
# else:
#     return tensor
