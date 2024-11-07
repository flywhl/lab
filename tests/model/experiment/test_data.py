import pytest
import torch
from pydantic import BaseModel, ConfigDict
from lab.model.experiment.experiment import Data


class TestData(Data):
    field1: torch.Tensor
    field2: torch.Tensor


def test_data_stack_single_item():
    data = TestData(field1=torch.tensor([1, 2, 3]), field2=torch.tensor([4, 5, 6]))
    result = data.stack([])
    assert torch.all(result.field1.eq(torch.tensor([1, 2, 3])))
    assert torch.all(result.field2.eq(torch.tensor([4, 5, 6])))


def test_data_stack_multiple_items():
    data1 = TestData(field1=torch.tensor([1, 2, 3]), field2=torch.tensor([4, 5, 6]))
    data2 = TestData(field1=torch.tensor([7, 8, 9]), field2=torch.tensor([10, 11, 12]))
    data3 = TestData(
        field1=torch.tensor([13, 14, 15]), field2=torch.tensor([16, 17, 18])
    )

    result = data1.stack([data2, data3])

    assert torch.all(
        result.field1.eq(torch.tensor([[1, 2, 3], [7, 8, 9], [13, 14, 15]]))
    )
    assert torch.all(
        result.field2.eq(torch.tensor([[4, 5, 6], [10, 11, 12], [16, 17, 18]]))
    )


def test_data_stack_different_shapes():
    data1 = TestData(field1=torch.tensor([[1, 2], [3, 4]]), field2=torch.tensor([5, 6]))
    data2 = TestData(
        field1=torch.tensor([[7, 8], [9, 10]]), field2=torch.tensor([11, 12])
    )

    result = data1.stack([data2])

    assert torch.all(
        result.field1.eq(torch.tensor([[[1, 2], [3, 4]], [[7, 8], [9, 10]]]))
    )
    assert torch.all(result.field2.eq(torch.tensor([[5, 6], [11, 12]])))


def test_data_stack_type_mismatch():
    class OtherData(BaseModel):
        model_config = ConfigDict(arbitrary_types_allowed=True)
        field3: torch.Tensor

    data = TestData(field1=torch.tensor([1, 2, 3]), field2=torch.tensor([4, 5, 6]))
    other = OtherData(field3=torch.tensor([7, 8, 9]))

    with pytest.raises(AttributeError):
        data.stack([other])  # type: ignore
