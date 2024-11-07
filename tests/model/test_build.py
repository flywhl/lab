from pathlib import Path
from torch import Tensor
from lab.model import Model
import yaml

from lab.model.network.network import Network


def test_model_build():
    class MyModel(Model):
        t: Tensor
        tau: float
        name: str

    class ParentModel(Model):
        submodel: list[MyModel]
        nested: dict[str, dict[str, MyModel]]
        foo: float

    data = {
        "tau": 5,
        "name": "Rory",
    }

    parent_data = {"submodel": [data], "foo": 10, "nested": {"a": {"b": data}}}

    model = ParentModel.build(parent_data)
    print(model)

    model_data = model.model_dump()

    new_model = ParentModel.build(model_data)

    print(new_model)


def test_network_build():
    file = Path(".") / "spec" / "experiment" / "propagate" / "adhoc.yaml"
    data = yaml.safe_load(file.open())["network"]
    network = Network.build(data)
    # print(network)

    print(network.model_dump_json(indent=2))
