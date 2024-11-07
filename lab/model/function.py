from typing import Optional, cast

import numpy as np
from torch import Tensor
import torch
from lab.model.dataset.dataset import Dataset
from lab.model.network.dendrites import Dendrite
from lab.model.network.population import CellParameters, PopulationState, Voltage
from lab.model.util import SuperSpike
from lab.model.util import milli


def load_chewie(dataset: Dataset):
    file = np.load(dataset.loc, allow_pickle=True).item()
    train = file["train"]
    test = file["test"]

    dataset._train_data = torch.as_tensor(train["stimulus"])
    dataset._train_labels = torch.as_tensor(train["velocity"])

    dataset._test_data = torch.as_tensor(test["stimulus"])
    dataset._test_labels = torch.as_tensor(test["velocity"])


def load_dummy(dataset: Dataset):
    train_data = np.random.rand(800, 10)  # Example: 800 samples, 10 features
    test_data = np.random.rand(200, 10)  # Example: 200 samples, 10 features
    train_labels = np.random.randint(0, 2, 800)  # Binary labels for train
    test_labels = np.random.randint(0, 2, 200)  # Binary labels for test

    dataset._train_data = torch.tensor(train_data, dtype=torch.float32)
    dataset._test_data = torch.tensor(test_data, dtype=torch.float32)
    dataset._train_labels = torch.tensor(train_labels, dtype=torch.long)
    dataset._test_labels = torch.tensor(test_labels, dtype=torch.long)


def activate(
    v: torch.Tensor, v_params: Voltage, activation: str, alpha: float = 100.0
) -> tuple[torch.Tensor, torch.Tensor]:
    if activation == "identity":
        z = v
    elif activation == "tanh":
        z = torch.tanh(v)
    elif activation == "relu":
        z = torch.relu(v)
    elif activation == "rectified_tanh":
        z = torch.relu(torch.tanh(v))
    elif activation == "spk":
        z = cast(Tensor, SuperSpike.apply(v - v_params.threshold, alpha))
        v = ((1 - z.detach()) * v) + (z.detach() * v_params.v_reset)
    else:
        raise ValueError(f"Invalid activation: {activation}")

    return z, v


def _synapse_update(
    current: Tensor,
    dendrites: list[Dendrite],
    params: CellParameters,
    debug: bool = False,
) -> list[Tensor]:
    synaptic_currents = []
    jumps = current
    for i, dendrite in enumerate(dendrites):
        instant_current = dendrite.current

        jumps[:, :, i] += instant_current.squeeze(2)  # .squeeze(0)
        tau_inv = 1 / (dendrite.tau * milli)
        decay = -params.dt * tau_inv * jumps[:, :, i]

        synaptic_currents.append(jumps[:, :, i] + decay)

    return synaptic_currents


def li_step(
    ff_dendrites: list[Dendrite],
    local_dendrites: list[Dendrite],
    params: CellParameters,
    state: Optional[PopulationState] = None,
) -> PopulationState:
    v_idx = 0
    dt = params.dt
    if not state:
        raise RuntimeError("Do not want.")

    ### SYNAPTIC CURRENTS
    local_synaptic_currents = _synapse_update(
        state.i_syn_local, local_dendrites, params
    )
    ff_synaptic_currents = _synapse_update(state.i_syn_ff, ff_dendrites, params)

    ### INTRINSIC CURRENTS
    intrinsic_currents = []
    for i, conductance in enumerate(params.conductances):
        current = state.i_intrinsic[:, i]
        tau_inv = dt / (conductance.tau * milli)
        dc = tau_inv * (
            (conductance.a * (state.v[:, :, v_idx] - conductance.v_eq)) - current
        )
        c_new = current + dc
        intrinsic_currents.append(c_new)

    ### VOLTAGE
    voltage = params.voltages[v_idx]
    dv = (params.dt / (voltage.tau * milli)) * (
        -(state.v[:, :, v_idx] - voltage.v_reset)
        + state.i_syn_ff.sum(dim=2)
        + state.i_syn_local.sum(dim=2)
        + state.i_intrinsic.sum(dim=2)
    )
    v_new = state.v
    v_new[:, :, v_idx] += dv

    ### SPIKES
    z, v = activate(v_new, voltage, params.activation)

    i_syn_local = (
        torch.stack(local_synaptic_currents, dim=2)
        if len(local_synaptic_currents) > 0
        else torch.tensor(local_synaptic_currents).reshape(state.i_syn_local.shape)
    )
    i_intrinsic = (
        torch.stack(intrinsic_currents, dim=2)
        if len(intrinsic_currents) > 0
        else torch.tensor(intrinsic_currents).reshape(state.i_intrinsic.shape)
    )

    return PopulationState(
        spk=z,
        v=v,
        i_syn_ff=torch.stack(ff_synaptic_currents, dim=2),  # B x C x N
        i_syn_local=i_syn_local,  # B x C x N
        i_intrinsic=i_intrinsic,
    )


def step(
    ff_dendrites: list[Dendrite],
    local_dendrites: list[Dendrite],
    params: CellParameters,
    state: Optional[PopulationState] = None,
) -> PopulationState:
    dt = params.dt
    if not state:
        raise RuntimeError("Do not want.")

    ### SYNAPTIC CURRENTS
    local_synaptic_currents = _synapse_update(
        state.i_syn_local, local_dendrites, params
    )
    ff_synaptic_currents = _synapse_update(
        state.i_syn_ff, ff_dendrites, params, debug=False
    )

    ### INTRINSIC CURRENTS
    intrinsic_currents = []
    for i, conductance in enumerate(params.conductances):
        current = state.i_intrinsic[:, :, i]
        tau_inv = dt / (conductance.tau * milli)
        dc = tau_inv * (
            (conductance.a * (state.v[:, :, 0] - conductance.v_eq)) - current
        )
        c_new = current + dc
        intrinsic_currents.append(c_new)

    try:
        ### VOLTAGE
        v_idx = 0
        voltage = params.voltages[v_idx]
        dv = (params.dt / (voltage.tau * milli)) * (
            -(state.v[:, :, v_idx] - voltage.v_reset)
            + state.i_syn_ff.sum(dim=2)
            + state.i_syn_local.sum(dim=2)
            + state.i_intrinsic.sum(dim=2)  # TODO(urgent): dim=0 or 1?
        )
        v_new = state.v
        v_new[:, :, v_idx] += dv
    except:
        raise

    ### SPIKES
    z, v = activate(v_new, voltage, params.activation)

    return PopulationState(
        spk=z,
        v=v,
        i_syn_ff=torch.stack(ff_synaptic_currents, dim=2),  # B x C x N
        i_syn_local=torch.stack(local_synaptic_currents, dim=2),  # B x C x N
        i_intrinsic=torch.stack(intrinsic_currents, dim=2),
    )
