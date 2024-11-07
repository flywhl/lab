from enum import Enum
from pathlib import Path
from types import ModuleType
from typing import Any, Self, get_args, get_origin
from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    FieldSerializationInfo,
    field_serializer,
)
from pydantic.fields import FieldInfo
from torch import Tensor
import torch
from torch.nn import Parameter
import numpy as np
import importlib
import yaml


class ResolvableFieldInfo(FieldInfo):
    def __init__(self, module: ModuleType, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self._lab_module = module


class Parity(Enum):
    POS = 1
    NEG = -1
    MIX = None


class Initialisation(BaseModel): ...


class GaussianInitialisation(Initialisation):
    mean: float
    var: float


class TensorSpec(BaseModel):
    value: float | str | None = None
    init: GaussianInitialisation | None = None
    shape: tuple[int, ...] | None = None
    parity: Parity | None = None
    density: float | None = None

    def build(self) -> Tensor:
        shape = self.shape or (1,)
        if self.init:
            t = torch.normal(mean=self.init.mean, std=self.init.var, size=shape)
        else:
            assert self.value, "If no init, you must give a value for the Tensor"
            # TODO
            value = self.value  # or self.build(self.value)
            if isinstance(value, str):
                raise NotImplementedError("TODO: process string-value for Tensor")

            t = torch.full(shape, value)

        t = Parameter(t, requires_grad=True)
        if self.density:
            density_mask = (
                torch.rand(t.shape, requires_grad=False, device=None) < self.density
            ).float()
            t.data *= density_mask
            t.register_hook(lambda grad: grad * density_mask)

        if self.parity:
            t.data = t.data.abs()

        return t


class Model(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    @field_serializer("*")
    def serialize_tensor(self, v, _info: FieldSerializationInfo):
        if isinstance(v, (Tensor, Parameter)):
            return v.tolist()
        return v

    @classmethod
    def _process_val_reference(cls, path: str, total_data: dict[str, Any]) -> Any:
        keys = path.split(".")
        value = total_data
        for key in keys:
            if "[" in key and "]" in key:
                key, index = key.split("[")
                index = int(index.rstrip("]"))
                value = value[key][index]
            else:
                value = value[key]
        return value

    @classmethod
    def _process_import_reference(cls, path: str) -> Any:
        module_path, attr = path.rsplit(".", 1)
        module = importlib.import_module(module_path)
        return getattr(module, attr)

    @classmethod
    def _process_spec_reference(cls, path: Path) -> Any:
        return yaml.safe_load(path.read_text())

    @classmethod
    def _process_reference(cls, reference: str, total_data: dict[str, Any]) -> Any:
        ref_type, ref_value = reference.split(":")
        if ref_type == "val":
            return cls._process_val_reference(ref_value, total_data)
        elif ref_type == "import":
            return cls._process_import_reference(ref_value)
        elif ref_type == "spec":
            return cls._process_spec_reference(Path(ref_value))
        else:
            raise ValueError(f"Unknown reference type: {ref_type}")

    @classmethod
    def _preprocess(
        cls, data: dict[str, Any], total_data: dict[str, Any]
    ) -> dict[str, Any]:
        for field_name, field_info in cls.model_fields.items():
            type_ = field_info.annotation
            assert type_, "Missing annotation?"

            try:
                field_data = data[field_name]
            except KeyError:
                required = field_info.is_required() and get_origin(type_) not in (
                    dict,
                    list,
                )
                if required:
                    raise
                # TODO: make this more robust
                data[field_name] = (
                    {}
                    if get_origin(type_) is dict
                    else []
                    if get_origin(type_) is list
                    else None
                )
                continue

            if isinstance(field_data, str) and field_data.startswith("@"):
                data[field_name] = cls._process_reference(field_data[1:], total_data)
            elif get_origin(type_) is tuple and isinstance(field_data, (list, tuple)):
                # TODO: check for Model nested
                # data[field_name] = field_data
                data[field_name] = [
                    cls._process_reference(item[1:], total_data)
                    if isinstance(item, str) and item.startswith("@")
                    else item
                    for item in field_data
                ]
            elif get_origin(type_) is list and isinstance(field_data, list):
                generic_type = get_args(type_)[0]
                if issubclass(generic_type, Model):
                    data[field_name] = [
                        generic_type._preprocess(list_data, total_data)
                        for list_data in field_data
                    ]
            elif get_origin(type_) is dict and isinstance(field_data, dict):
                generic_type = get_args(type_)[1]
                if get_origin(generic_type) is dict:
                    inner_generic_type = get_args(generic_type)[1]
                    if issubclass(inner_generic_type, Model):
                        data[field_name] = {
                            k: {
                                inner_k: inner_generic_type._preprocess(
                                    inner_data, total_data
                                )
                                for inner_k, inner_data in v.items()
                            }
                            for k, v in field_data.items()
                        }
                elif issubclass(generic_type, Model):
                    data[field_name] = {
                        k: generic_type._preprocess(dict_data, total_data)
                        for k, dict_data in field_data.items()
                    }
            elif issubclass(type_, Model) and isinstance(field_data, dict):
                data[field_name] = type_._preprocess(field_data, total_data)
            elif type_ is Tensor:
                if isinstance(field_data, Tensor):
                    tensor = field_data
                elif isinstance(field_data, (int, float)):
                    tensor = torch.as_tensor(field_data)
                elif isinstance(field_data, (list, np.ndarray)):
                    tensor = torch.as_tensor(field_data)
                else:
                    tensor = TensorSpec(**field_data)
                    # tensor = TensorSpec(**data, init=data[field_name]).build()

                data[field_name] = tensor

        return data

    @classmethod
    def build(cls, data: dict[str, Any]) -> Self:
        data = cls._preprocess(data, data)

        return cls.model_validate(data)

    # @classmethod
    # def spec(cls) -> Type[Spec]:
    #     """
    #
    #     class MyExperiment(Model):
    #         network: Network  <- create a spec for this first
    #         dataset: Dataset
    #         loss: Loss
    #         hypers: Hypers
    #     """
    #     spec_module = importlib.import_module("lab.model.spec.network")
    #
    #     fields = {}
    #     for field_name, field_info in cls.model_fields.items():
    #         field_type = field_info.annotation
    #         if not field_type:
    #             raise ValueError(f"No annotation for {field_name}?")
    #
    #         if issubclass(field_type, Model):
    #             # we have a Model and can generate a Spec
    #             field_spec = field_type.spec()
    #         elif field_type is list:
    #             ...
    #         elif field_type is dict:
    #             ...
    #         elif hasattr(field_info, "_lab_module"):
    #             ...
    #
    #         spec_class_name = f"{field_name.capitalize()}Spec"
    #         spec_class = getattr(spec_module, spec_class_name, None)
    #
    #         if spec_class and issubclass(spec_class, Spec):
    #             fields[field_name] = (spec_class, field_info.default)
    #         else:
    #             fields[field_name] = (field_info.annotation, field_info)
    #
    #     DynamicSpec = create_model(f"{cls.__name__}Spec", __base__=Spec, **fields)
    #
    #     def build(self, **_) -> Experiment:
    #         def _acquire_build_arg(v: Any, components: dict):
    #             if isinstance(v, str) and v.startswith("method:"):
    #                 path = v.split(":")[1].split(".")
    #                 method = getattr(components[path[0]], path[1])
    #                 return method()
    #
    #             return v
    #
    #         # Build all the components
    #         components = {}
    #         for field_name, _ in self.model_fields.items():
    #             spec_value = getattr(self, field_name)
    #             if isinstance(spec_value, Spec):
    #                 build_args = {
    #                     k: _acquire_build_arg(v, components)
    #                     for k, v in getattr(spec_value, "args", {}).items()
    #                 }  # {'params': 'method:network.parameters', ...)
    #                 components[field_name] = spec_value.build(**build_args)
    #             else:
    #                 components[field_name] = spec_value
    #
    #         return cls(**components)
    #
    #     setattr(DynamicSpec, "build", build)
    #
    #     return DynamicSpec
