import pytest
import torch
from pathlib import Path
from lab.model.dataset.dataset import Dataset
from tests.model.spec.func import load_dummy


@pytest.fixture
def dataset():
    return Dataset(loc=Path("/tmp/test_dataset"), load_data=load_dummy)


def test_dataset_initialization(dataset: Dataset):
    assert isinstance(dataset, Dataset)
    assert dataset.loc == Path("/tmp/test_dataset")
    assert dataset._mode == "train"


def test_dataset_train_test_properties(dataset: Dataset):
    assert dataset._mode == "train"

    test_dataset = dataset.test(batch=8, shuffle=True)
    assert dataset._mode == "test"
    assert test_dataset.dataset is dataset

    train_dataset = dataset.train(batch=8, shuffle=True)
    assert dataset._mode == "train"
    assert train_dataset.dataset is dataset


def test_dataset_length(dataset: Dataset):
    total_train, total_test = 800, 200
    batch = 8
    assert len(dataset.train(batch=batch, shuffle=True)) == total_train // batch
    assert len(dataset.test(batch=batch, shuffle=True)) == total_test // batch


def test_dataset_getitem(dataset: Dataset):
    train_item = next(iter(dataset.train(batch=8, shuffle=True)))
    assert isinstance(train_item, list)
    assert len(train_item) == 2
    assert isinstance(train_item[0], torch.Tensor)
    assert isinstance(train_item[1], torch.Tensor)
    assert train_item[0].shape == (8, 10)
    assert train_item[1].shape == (8,)

    test_item = next(iter(dataset.test(batch=8, shuffle=True)))
    assert isinstance(test_item, list)
    assert len(test_item) == 2
    assert isinstance(test_item[0], torch.Tensor)
    assert isinstance(test_item[1], torch.Tensor)
    assert test_item[0].shape == (8, 10)
    assert test_item[1].shape == (8,)


def test_dataset_data_types(dataset: Dataset):
    train_data, train_label = next(iter(dataset.train(batch=8, shuffle=True)))
    assert train_data.dtype == torch.float32
    assert train_label.dtype == torch.long

    test_data, test_label = next(iter(dataset.test(batch=8, shuffle=True)))
    assert test_data.dtype == torch.float32
    assert test_label.dtype == torch.long


def test_dataset_data_ranges(dataset: Dataset):
    train_data, train_label = next(iter(dataset.train(batch=8, shuffle=True)))
    assert 0 <= train_data.min() and train_data.max() <= 1
    assert all(label in [0, 1] for label in train_label)

    test_data, test_label = next(iter(dataset.test(batch=8, shuffle=True)))
    assert 0 <= test_data.min() and test_data.max() <= 1
    assert all(label in [0, 1] for label in test_label)
