import torch
from torch import Tensor
import math
import matplotlib.pyplot as plt
from typing import List, Optional
from lab.model.experiment.experiment import (
    Experiment,
    Hypers as LabHypers,
    Data as LabData,
)
from lab.model.network.layer import LayerState
from lab.model.network.network import Network
from lab.model.util import Vary


class Data(LabData):
    output_max_voltage: Tensor
    vary: Optional[Vary] = None

    def plot(self):
        if self.vary is None:
            return
        fig, ax = plt.subplots()

        mean = self.output_max_voltage.mean(dim=1).detach()
        std = torch.sqrt(self.output_max_voltage.var(dim=1).detach())

        ax.plot(self.vary.values, mean, label="mean", color="blue")
        ax.fill_between(
            self.vary.values,
            mean - std,
            mean + std,
            alpha=0.3,
            color="blue",
            label="±1 std dev",
        )

        ax.set_title(f"{self.vary.param}")
        ax.set_xlabel(self.vary.param)
        ax.set_ylabel("mV (output max.)")
        ax.legend()
        fig.tight_layout()
        fig.savefig("output_max_voltage.png")
        plt.close(fig)

        # print(f"Vary param: {self.vary.param}")
        # print(self.output_max_voltage.shape)
        # # assert self.output_max_voltage.dim() == 2
        #
        # print(f"Mean\tOutputMaxVoltage: {self.output_max_voltage.mean():.2f}")
        # print(f"Variance\t OutputMaxVoltage: {self.output_max_voltage.var():.2f}")


class Hypers(LabHypers):
    dt: float
    ampl: float
    freq: float
    duration: float
    pulse_ampl: float
    pulse_duration: float


@Experiment.register("propagate")
class Propagate(Experiment[Hypers, Data]):
    """Simulate an input pulse propagating through multiple oscillating layers of a network.

    Each trial should be 1000 ms long.

    The first layer should receive a 100 ms pulse as input.

    Later layers should receive a sine wave (ampl/freq from hypers) as input, alongside forward-propagating spikes.

    We want to measure how many layers produce a spike (i.e. how far the pulse propagates).
    """

    network: Network
    hypers: Hypers

    def run(self, hypers: Hypers) -> Data:
        self.hypers = hypers
        num_steps = int(self.hypers.duration / self.hypers.dt)
        print(f"Simulating {num_steps} time steps.\n")

        pulse = self._create_pulse(num_steps, hypers.pulse_ampl)
        sine_waves = [
            self._sine_wave(
                duration=self.hypers.duration,
                shape=(1,),
                ampl=self.hypers.ampl,
                freq=self.hypers.freq,
            )
            for _ in range(len(self.network.layers) - 2)
        ]

        layer_inputs = [pulse] + sine_waves
        layer_states = self.network.forward(*layer_inputs)

        self._plot_state(layer_states)
        self._plot_inputs(pulse, sine_waves)

        output_max_voltage = layer_states[-1]["pop"].v.max().detach().clone()
        del layer_states

        return Data(output_max_voltage=output_max_voltage)

    ### DATA ###

    def _create_pulse(self, num_steps: int, ampl: float) -> Tensor:
        pulse_steps = int(self.hypers.pulse_duration / self.hypers.dt)
        pulse = torch.zeros(num_steps, 1, 1)
        start_step = int((self.hypers.duration / 2) / self.hypers.dt)
        pulse[start_step : start_step + pulse_steps, :, :] = ampl
        return pulse

    def _sine_wave(
        self, duration: float, shape: tuple, ampl: float, freq: float
    ) -> Tensor:
        num_steps = int(duration / self.hypers.dt)
        t = torch.arange(0, duration, self.hypers.dt)
        phase = (
            2 * math.pi * torch.rand(shape)
        )  # Random phase for each element in shape
        sine_wave = ampl * torch.sin(
            2 * math.pi * freq * t.unsqueeze(-1).unsqueeze(-1) + phase
        )
        return sine_wave.expand(num_steps, 1, *shape)

    ### PLOTS ###

    def _plot_inputs(self, pulse: Tensor, sine_waves: List[Tensor]):
        num_inputs = 1 + len(sine_waves)
        fig, axes = plt.subplots(
            num_inputs, 1, figsize=(10, 4 * num_inputs), sharex=True
        )

        time = torch.arange(0, self.hypers.duration, self.hypers.dt)

        # Plot pulse
        axes[0].plot(time, pulse.squeeze())
        axes[0].set_ylabel("Pulse")
        axes[0].set_title("Input Signals")

        # Plot sine waves
        for i, sine_wave in enumerate(sine_waves):
            axes[i + 1].plot(time, sine_wave.squeeze())
            axes[i + 1].set_ylabel(f"Sine Wave {i+1}")

        axes[-1].set_xlabel("Time (s)")
        plt.tight_layout()
        plt.savefig("input_signals.png")
        plt.close()

    def _plot_state(self, layer_states: list[LayerState]):
        num_layers = len(layer_states)
        fig, axes = plt.subplots(
            num_layers, 1, figsize=(10, 4 * num_layers), sharex=True
        )

        time = torch.arange(0, self.hypers.duration, self.hypers.dt)

        for i, layer_state in enumerate(layer_states):
            ax = axes[i] if num_layers > 1 else axes
            # ax.set_ylim(-100, -30)

            for pop_name, pop_state in layer_state.items():
                voltage = pop_state.v.squeeze().detach().cpu().numpy()

                ax.plot(time, voltage)

            ax.set_ylabel(f"Layer {i+1}\nVoltage")
            # ax.legend()

        axes[-1].set_ylim(0, 20)
        axes[-1].set_xlabel("Time (s)")
        plt.tight_layout()
        plt.savefig("layer_voltages.png")
        plt.close()

    def _calculate_max_output(self, layer_states: list) -> int:
        depth = 0
        for layer_state in layer_states:
            if any(torch.any(pop_state.spk > 0) for pop_state in layer_state.values()):
                depth += 1
            else:
                break
        return depth

    def save(self):
        # Placeholder for saving functionality
        pass

    def checkpoint(self, data: Data, name: str):
        # Placeholder for checkpointing functionality
        pass
