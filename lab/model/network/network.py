from __future__ import annotations
from pathlib import Path
from typing import TYPE_CHECKING, TypeVar, Unpack

from torch import Tensor

from lab.model.network.layer import Layer
from lab.model import Model

if TYPE_CHECKING:
    from lab.model.network.layer import LayerState


L = TypeVar("L", bound=Layer)


class Network(Model):
    layers: list[Layer]
    shape: tuple[dict[str, int], ...]  # TODO

    def forward(self, *input: Tensor):
        """Forward pass

        input: B x N x T
        """
        assert len(input) >= 1
        T, B, _ = input[0].shape
        layer_states: list[LayerState] = [
            layer.initial_state(n_batch=B, pop_units=self.shape[1:][i])
            for i, layer in enumerate(self.layers)
        ]

        total_layer_states = [
            layer.initial_state(
                n_time=T,
                n_batch=B,
                pop_units=self.shape[1:][i],
                initialisation="empty",
            )
            for i, layer in enumerate(self.layers)
        ]

        for ts in range(T):
            layer_input: dict[str, Tensor] = {}
            for i, (layer, layer_state, total_layer_state) in enumerate(
                zip(self.layers, layer_states, total_layer_states)
            ):
                if len(input) > i:
                    layer_input["stimulus"] = input[i][ts].unsqueeze(0)
                layer_state = layer.forward(layer_input, layer_state)
                for pop, pop_total in zip(
                    layer_state.values(), total_layer_state.values()
                ):
                    pop_total.insert_state(pop, at_timestep=ts)

                layer_input = {name: pop.spk for name, pop in layer_state.items()}

        return total_layer_states

    def post_step(self):
        """Run any post-simulation processes."""

    def parameters(self) -> dict[str, Tensor]:
        layer_params = [layer.parameters for layer in self.layers]
        all_params = {k: v for d in layer_params for k, v in d.items()}

        return all_params

    # def save(self, loc: Path):
    #     for synapse in self.synapses:
    #         if synapse is None:
    #             continue
    #         synapse.save(loc)

    def load(self, loc: Path, dt: float) -> "Network":
        raise NotImplementedError()
