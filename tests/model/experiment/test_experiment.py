import torch
import pytest
from lab.model.experiment import experiment


class Data(experiment.Data):
    tensor_field: torch.Tensor
    scalar_field: torch.Tensor

    def plot(self): ...


class Hypers(experiment.Hypers):
    ampl: float = 1.0
    freq: tuple | float = (0.1, 1.0)


class TestExperiment(experiment.Experiment[Hypers, Data]):
    def run(self, hypers: Hypers) -> Data:
        return Data(
            tensor_field=torch.rand(3, 4) * hypers.ampl,
            scalar_field=torch.rand(1) * hypers.ampl,
        )

    def checkpoint(self, data: Data, name: str):
        pass

    def save(self):
        pass


def test_experiment_call():
    experiment = TestExperiment(hypers=Hypers())

    # Test with K=1 (default behavior)
    result = experiment()
    assert isinstance(result, Data)
    assert result.tensor_field.shape == (3, 4)
    assert isinstance(result.scalar_field, torch.Tensor)
    assert result.scalar_field.shape == (1,)

    # Test with K=3
    result = experiment(K=3)
    assert isinstance(result, Data)
    assert result.tensor_field.shape == (3, 3, 4)
    assert isinstance(result.scalar_field, torch.Tensor)
    assert result.scalar_field.shape == (3, 1)

    # Test that each run produces different random tensors
    assert not torch.allclose(result.tensor_field[0], result.tensor_field[1])
    assert not torch.allclose(result.tensor_field[1], result.tensor_field[2])
    assert not torch.allclose(result.tensor_field[0], result.tensor_field[2])


def test_experiment_call_with_varying_param():
    experiment = TestExperiment(hypers=Hypers())

    # Test with varying 'freq' parameter
    result = experiment(K=5, vary="freq")
    assert isinstance(result, Data)
    assert result.tensor_field.shape == (5, 3, 4)
    assert isinstance(result.scalar_field, torch.Tensor)
    assert result.scalar_field.shape == (5, 1)

    # Check that scalar_field values are different (due to varying parameter)
    assert len(torch.unique(result.scalar_field)) == 5

    # Test with non-existent parameter
    with pytest.raises(ValueError):
        experiment(K=3, vary="non_existent_param")

    # Test with non-tuple parameter
    with pytest.raises(ValueError):
        experiment.hypers.ampl = 1.0
        experiment(K=3, vary="ampl")


def test_hypers_with_value():
    hypers = Hypers(ampl=1.0, freq=(0.1, 1.0))

    # Test updating a single value
    new_hypers = hypers.with_value({"ampl": 2.0})
    assert new_hypers.ampl == 2.0
    assert new_hypers.freq == (0.1, 1.0)
    assert isinstance(new_hypers, Hypers)

    # Test updating multiple values
    new_hypers = hypers.with_value({"ampl": 3.0, "freq": (0.2, 2.0)})
    assert new_hypers.ampl == 3.0
    assert new_hypers.freq == (0.2, 2.0)

    # Test that the original hypers object is unchanged
    assert hypers.ampl == 1.0
    assert hypers.freq == (0.1, 1.0)

    # Test with an invalid field name
    # with pytest.raises(ValueError):
    #     hypers.with_value({"invalid_field": 5.0})

    # Test type conversion
    new_hypers = hypers.with_value({"ampl": "2.5"})
    assert new_hypers.ampl == 2.5
    assert isinstance(new_hypers.ampl, float)

    new_hypers = hypers.with_value({"freq": 2.0})
    assert new_hypers.freq == 2.0
