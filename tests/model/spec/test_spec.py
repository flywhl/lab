from pathlib import Path
from typing import Callable
import pytest
import yaml

from lab.model.experiment.train import SupervisedTrainingSpec

from . import func


@pytest.fixture
def supervised_training_spec():
    specfile = Path(__file__).parent / "test.yaml"
    data = yaml.safe_load(specfile.read_text())
    namespaces = {Callable: func}
    experiment_spec = SupervisedTrainingSpec.parse_with_namespaces(data, namespaces)

    return experiment_spec


def test_load_experiment_from_yaml_should_succeed():
    print()
    specfile = Path(__file__).parent / "test.yaml"
    data = yaml.safe_load(specfile.read_text())
    namespaces = {Callable: func}
    experiment_spec = SupervisedTrainingSpec.parse_with_namespaces(data, namespaces)

    experiment_spec.build()
