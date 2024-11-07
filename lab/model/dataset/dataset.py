from pathlib import Path
from typing import Callable, Literal, Any
from pydantic import PrivateAttr
from torch import Tensor
from torch.utils.data import DataLoader, Dataset as TorchDataset

from lab.model import Model


class Dataset(Model, TorchDataset):
    loc: Path
    load_data: Callable[["Dataset"], None]

    _mode: Literal["train", "test"] = PrivateAttr(default="train")
    _train_data: Tensor = PrivateAttr()
    _test_data: Tensor = PrivateAttr()
    _train_labels: Tensor = PrivateAttr()
    _test_labels: Tensor = PrivateAttr()

    def model_post_init(self, _: Any) -> None:
        self.load_data(self)

    def train(self, batch: int, shuffle: bool) -> DataLoader:
        self._mode = "train"
        dataloader = DataLoader(self, batch_size=batch, shuffle=shuffle)

        return dataloader

    def test(self, batch: int, shuffle: bool) -> DataLoader:
        self._mode = "test"
        dataloader = DataLoader(self, batch_size=batch, shuffle=shuffle)

        return dataloader

    def __getitem__(self, idx: int):
        if self._mode == "train":
            return self._train_data[idx], self._train_labels[idx]
        else:
            return self._test_data[idx], self._test_labels[idx]

    def __len__(self):
        return len(self._train_data) if self._mode == "train" else len(self._test_data)
