from abc import ABC, abstractmethod
from typing import (
    Any,
    ClassVar,
    Dict,
    Generic,
    Self,
    Sequence,
    Type,
    Optional,
    TypeVar,
)
import importlib

from pydantic import create_model
import torch

from lab.model import Model
from lab.model.spec.network import Spec
from lab.model.util import Vary


class Hypers(ABC, Model):
    def with_value(self, updates: dict[str, Any]) -> Self:
        current_values = self.model_dump()
        current_values.update(updates)
        return self.model_validate(current_values)


class Data(ABC, Model):
    @abstractmethod
    def plot(self): ...

    def stack(self, others: Sequence["Data"], **extra: Any) -> Self:
        stacked = {}
        print(f"Extra: {', '.join(extra.keys())}")
        for field, info in self.model_fields.items():
            print(f"\t...{field}")
            if info.annotation != torch.Tensor or field in extra:
                print("\t\tskipping.")
                continue
            values = [getattr(self, field)] + [
                getattr(other, field) for other in others
            ]
            stacked[field] = torch.stack(values, dim=0)

        stacked.update(extra)
        return self.__class__(**stacked)


H = TypeVar("H", bound=Hypers)
D = TypeVar("D", bound=Data)


class Experiment(ABC, Model, Generic[H, D]):
    """Base class for experiments"""

    _registry: ClassVar[dict[str, Type["Experiment"]]] = {}

    hypers: H

    @abstractmethod
    def run(self, hypers: H) -> D: ...

    @abstractmethod
    def checkpoint(self, data: D, name: str): ...

    @abstractmethod
    def save(self): ...

    def __call__(self, K: int = 1, vary: Optional[Vary] = None) -> D:
        if vary:
            return self._run_with_varying_param(K, vary)
        else:
            return self._run_multiple(K, self.hypers)

    def _run_multiple(self, K: int, hypers: H) -> D:
        results = []
        for _ in range(K):
            result = self.run(hypers)
            results.append(result)

        return self._stack_results(results)

    def _run_with_varying_param(self, K: int, vary: Vary) -> D:
        if not hasattr(self.hypers, vary.param):
            raise ValueError(f"Parameter {vary.param} not found in Hypers")

        values = vary.values

        results = []
        for value in values.tolist():
            new_hypers = self.hypers.with_value({vary.param: value})
            result = self._run_multiple(K=K, hypers=new_hypers)
            results.append(result)

        return self._stack_results(results, vary=vary)

    def _stack_results(self, results: Sequence[D], **extra: Any) -> D:
        if len(results) == 1:
            return results[0]
        return results[0].stack(results[1:], **extra)

    @classmethod
    def register(cls, name: str):
        def decorator(sub_class: Type["Experiment"]):
            cls._registry[name] = sub_class
            return sub_class

        return decorator

    @classmethod
    def get_registered_experiments(cls) -> Dict[str, Type["Experiment"]]:
        return cls._registry.copy()

    @classmethod
    def spec(cls) -> Type[Spec["Experiment"]]:
        spec_module = importlib.import_module("lab.model.spec.network")

        fields = {}
        for field_name, field_info in cls.model_fields.items():
            spec_class_name = f"{field_name.capitalize()}Spec"
            spec_class = getattr(spec_module, spec_class_name, None)

            if spec_class and issubclass(spec_class, Spec):
                fields[field_name] = (spec_class, field_info.default)
            else:
                fields[field_name] = (field_info.annotation, field_info)

        DynamicSpec = create_model(f"{cls.__name__}Spec", __base__=Spec, **fields)

        def build(self, **_) -> Experiment:
            def _acquire_build_arg(v: Any, components: dict):
                if isinstance(v, str) and v.startswith("method:"):
                    path = v.split(":")[1].split(".")
                    method = getattr(components[path[0]], path[1])
                    return method()

                return v

            # Build all the components
            components = {}
            for field_name, _ in self.model_fields.items():
                spec_value = getattr(self, field_name)
                if isinstance(spec_value, Spec):
                    build_args = {
                        k: _acquire_build_arg(v, components)
                        for k, v in getattr(spec_value, "args", {}).items()
                    }  # {'params': 'method:network.parameters', ...)
                    components[field_name] = spec_value.build(**build_args)
                else:
                    components[field_name] = spec_value

            return cls(**components)

        setattr(DynamicSpec, "build", build)

        return DynamicSpec
