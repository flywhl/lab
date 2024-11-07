from torch import Tensor
import torch
from torch.utils.data import DataLoader
from lab.model.dataset.dataset import Dataset
from lab.model.experiment.experiment import (
    Experiment,
    Hypers as LabHypers,
    Data as LabData,
)
import torch.nn as nn
import matplotlib.pyplot as plt

from torch.optim.optimizer import Optimizer

from lab.model.spec.network import Spec
from lab.model.network.network import Network


class Data(LabData):
    losses: Tensor

    def plot(self):
        fig, ax = plt.subplots()

        ax.plot(self.losses)


class Hypers(LabHypers):
    epochs: int
    lr: float
    batch: int
    dt: float



@Experiment.register("train")
class SupervisedTraining(Experiment[Hypers, Data]):
    """Train a model"""

    network: Network
    optimizer: Optimizer
    dataset: Dataset
    hypers: Hypers
    loss: nn.Module = nn.MSELoss()

    def run(self, hypers: Hypers) -> Data:
        losses = []
        train_loader = self.dataset.train(batch=self.hypers.batch, shuffle=True)

        for epoch in range(hypers.epochs):
            try:
                epoch_loss = self._do_epoch(train_loader)
                losses.append(epoch_loss)
                print(f"Epoch {epoch + 1}/{self.hypers.epochs}\t {epoch_loss:.4f}")
            except Exception as e:
                raise e

        return Data(losses=torch.as_tensor(losses))

    def _do_epoch(self, dataloader: DataLoader[Tensor]):
        epoch_loss = 0
        for i, (stimulus, velocity) in enumerate(dataloader):
            stimulus = stimulus.transpose(1, 0)
            velocity = velocity.transpose(1, 0)
            self.optimizer.zero_grad()

            # Assuming batch is the input and target (since our dataset generates both)
            outputs = self.network.forward(stimulus)
            output_layer = outputs[1]
            estimate = output_layer["pop"].v.squeeze()

            epoch_loss += self.loss(estimate, velocity).mean()

        return epoch_loss / len(dataloader)
        #     loss = self.criterion(outputs, targets)
        #
        #     loss.backward()
        #     self.optimizer.step()
        #
        #     total_loss += loss.item()
        #
        # return total_loss / len(dataloader)

    def save(self): ...

    def checkpoint(self, data: Data, name: str): ...

    @classmethod
    def from_spec(cls, spec: Spec) -> "SupervisedTraining":
        return spec.build()
