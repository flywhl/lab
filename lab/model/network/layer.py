from __future__ import annotations
import logging
from typing import TYPE_CHECKING, Literal
from abc import ABC
from torch import Tensor
from lab.model.network.dendrites import Dendrite
from lab.model import Model
from lab.model.network.population import CellParameters, PopulationState

if TYPE_CHECKING:
    from lab.model.spec.network import LayerSpec


logger = logging.getLogger(__name__)


LayerState = dict[str, PopulationState]


class LayerInput(ABC, Model):
    """Layer Input"""


class Layer(Model):
    populations: dict[str, CellParameters]

    # [to][from]
    ff_dendrites: dict[str, dict[str, Dendrite]]
    local_dendrites: dict[str, dict[str, Dendrite]]

    def forward(self, input: dict[str, Tensor], states: LayerState) -> LayerState:
        """Forward

        input: B x N

        @note: I don't know the types of the Populations - is that a problem?
        """

        for name, pop in self.populations.items():
            loaded_ff_dendrites = [
                dendrite.with_signal(input[ff_name])
                for ff_name, dendrite in self.ff_dendrites[name].items()
            ]
            loaded_local_dendrites = [
                dendrite.with_signal(states[from_].spk)
                for from_, dendrite in self.local_dendrites[name].items()
            ]

            states[name] = pop.step(
                loaded_ff_dendrites, loaded_local_dendrites, pop, states[name]
            )

        return states

    @classmethod
    def from_spec(cls, spec: "LayerSpec") -> "Layer":
        populations = {name: pop.build() for name, pop in spec.populations.items()}
        ff_dendrites = {
            to: {from_: dendrite.build() for from_, dendrite in from_dendrites.items()}
            for to, from_dendrites in spec.ff_dendrites.items()
        }

        local_dendrites = {
            pop: {
                from_: dendrite.build()
                for from_, dendrite in spec.local_dendrites.get(pop, {}).items()
            }
            for pop in spec.populations.keys()
        }

        return cls(
            populations=populations,
            ff_dendrites=ff_dendrites,
            local_dendrites=local_dendrites,
        )

    @property
    def parameters(self) -> dict[str, Tensor]:
        """Return all parameters in the layer

        @note
            TODO
        """
        params = {
            f"{from_name}_{to_name}": dendrite.weights
            for to_name, from_dendrites in self.local_dendrites.items()
            for from_name, dendrite in from_dendrites.items()
        }

        return params

    def _num_dendrites_local(self, pop: str) -> int:
        return len(self.local_dendrites[pop].values())

    def _num_dendrites_ff(self, pop: str) -> int:
        return len(self.ff_dendrites[pop].values())

    def initial_state(
        self,
        n_batch: int,
        pop_units: dict[str, int],
        initialisation: Literal["random", "empty"] = "random",
        n_time: int = 1,
    ) -> LayerState:
        return {
            name: pop.initial_state(
                n_batch=n_batch,
                n_syn_local=self._num_dendrites_local(name),
                n_syn_ff=self._num_dendrites_ff(name),
                n_time=n_time,
                n_units=pop_units[name],
                initialisation=initialisation,
            )
            for name, pop in self.populations.items()
        }
