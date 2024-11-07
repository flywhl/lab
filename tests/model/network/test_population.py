import pytest
import torch
from lab.model.network.population import PopulationState


def test_ensure_time():
    state = PopulationState.initial(
        n_v=2,
        n_units=5,
        n_syn_ff=2,
        n_syn_local=3,
        n_conductances=2,
        kind="empty",
    )

    original_dim = state.spk.dim()
    assert original_dim == 4  # T, B, E, N dimensions

    state_with_time = PopulationState.initial(
        n_v=2,
        n_units=5,
        n_syn_ff=2,
        n_syn_local=3,
        n_conductances=2,
        n_time=1,
        kind="empty",
    )

    assert state_with_time.spk.dim() == 4  # T, B, E, N dimensions
    time_state = state_with_time.ensure_time()
    assert time_state.spk.dim() == 4  # Should remain the same


def test_insert_state():
    # Create a base PopulationState
    base_state = PopulationState.initial(
        n_v=2,
        n_time=10,
        n_units=5,
        n_syn_ff=2,
        n_syn_local=3,
        n_conductances=2,
        kind="empty",
    )

    # Create an other PopulationState with time dimension
    other_state_with_time = PopulationState(
        v=torch.ones((3, 1, 2, 5)),
        i_syn_ff=torch.ones((3, 1, 2, 5)),
        i_syn_local=torch.ones((3, 1, 3, 5)),
        i_intrinsic=torch.ones((3, 1, 2, 5)),
        spk=torch.ones((3, 1, 1, 5)),
    )

    # Create an other PopulationState without time dimension
    other_state_without_time = PopulationState(
        v=torch.full((1, 2, 5), 2.0),
        i_syn_ff=torch.full((1, 2, 5), 2.0),
        i_syn_local=torch.full((1, 3, 5), 2.0),
        i_intrinsic=torch.full((1, 2, 5), 2.0),
        spk=torch.full((1, 1, 5), 2.0),
    )

    # Test inserting state with time dimension
    base_state.insert_state(other_state_with_time, at_timestep=2)
    assert torch.all(base_state.v[2:5] == 1.0)
    assert torch.all(base_state.i_syn_local[2:5] == 1.0)
    assert torch.all(base_state.i_syn_ff[2:5] == 1.0)
    assert torch.all(base_state.i_intrinsic[2:5] == 1.0)
    assert torch.all(base_state.spk[2:5] == 1.0)

    with pytest.raises(AssertionError):
        base_state.insert_state(other_state_without_time, at_timestep=6)

    # Test error when inserting at invalid timestep
    with pytest.raises(ValueError):
        base_state.insert_state(other_state_with_time, at_timestep=10)

    # Test error when base state doesn't have time dimension
    timeless_base_state = PopulationState(
        v=torch.zeros((1, 2, 5)),
        i_syn_local=torch.zeros((1, 3, 5)),
        i_syn_ff=torch.zeros((1, 2, 5)),
        i_intrinsic=torch.zeros((1, 2, 5)),
        spk=torch.zeros((1, 1, 5)),
    )
    with pytest.raises(
        AssertionError, match="Cannot insert into a PopulationState that has no time"
    ):
        timeless_base_state.insert_state(other_state_with_time, at_timestep=0)


def test_random_population_state():
    random_state = PopulationState.initial(
        n_batch=2,
        n_v=3,
        n_syn_local=2,
        n_syn_ff=2,
        n_conductances=1,
        n_units=10,
        n_time=5,
        kind="random",
    )

    assert random_state.v.shape == (5, 2, 3, 10)
    assert random_state.i_syn_local.shape == (5, 2, 2, 10)
    assert random_state.i_syn_ff.shape == (5, 2, 2, 10)
    assert random_state.i_intrinsic.shape == (5, 2, 1, 10)
    assert random_state.spk.shape == (5, 2, 1, 10)

    assert torch.all(random_state.v != 0)
    assert torch.all(random_state.i_syn_local != 0)
    assert torch.all(random_state.i_syn_ff != 0)
    assert torch.all(random_state.i_intrinsic != 0)
    assert torch.all(random_state.spk == 0)  # Spikes should be initialized to 0


def test_empty_population_state():
    empty_state = PopulationState.initial(
        n_batch=2,
        n_v=3,
        n_syn_local=2,
        n_syn_ff=2,
        n_conductances=1,
        n_units=10,
        n_time=5,
        kind="empty",
    )

    assert empty_state.v.shape == (5, 2, 3, 10)
    assert empty_state.i_syn_local.shape == (5, 2, 2, 10)
    assert empty_state.i_syn_ff.shape == (5, 2, 2, 10)
    assert empty_state.i_intrinsic.shape == (5, 2, 1, 10)
    assert empty_state.spk.shape == (5, 2, 1, 10)

    assert torch.all(empty_state.v == 0)
    assert torch.all(empty_state.i_syn_local == 0)
    assert torch.all(empty_state.i_syn_ff == 0)
    assert torch.all(empty_state.i_intrinsic == 0)
    assert torch.all(empty_state.spk == 0)


def test_insert_state_edge_cases():
    base_state = PopulationState(
        v=torch.zeros((10, 1, 2, 5)),
        i_syn_local=torch.zeros((10, 1, 3, 5)),
        i_syn_ff=torch.zeros((10, 1, 3, 5)),
        i_intrinsic=torch.zeros((10, 1, 2, 5)),
        spk=torch.zeros((10, 1, 1, 5)),
    )

    # Test inserting at the first timestep
    other_state = PopulationState(
        v=torch.ones((1, 1, 2, 5)),
        i_syn_local=torch.ones((1, 1, 3, 5)),
        i_syn_ff=torch.ones((1, 1, 3, 5)),
        i_intrinsic=torch.ones((1, 1, 2, 5)),
        spk=torch.ones((1, 1, 1, 5)),
    )
    base_state.insert_state(other_state, at_timestep=0)
    assert torch.all(base_state.v[0] == 1.0)
    assert torch.all(base_state.i_syn_local[0] == 1.0)
    assert torch.all(base_state.i_syn_ff[0] == 1.0)
    assert torch.all(base_state.i_intrinsic[0] == 1.0)
    assert torch.all(base_state.spk[0] == 1.0)

    # Test inserting at the last valid timestep
    other_state = PopulationState(
        v=torch.full((1, 1, 2, 5), 2.0),
        i_syn_local=torch.full((1, 1, 3, 5), 2.0),
        i_syn_ff=torch.full((1, 1, 3, 5), 2.0),
        i_intrinsic=torch.full((1, 1, 2, 5), 2.0),
        spk=torch.full((1, 1, 1, 5), 2.0),
    )
    base_state.insert_state(other_state, at_timestep=9)
    assert torch.all(base_state.v[9] == 2.0)
    assert torch.all(base_state.i_syn_local[9] == 2.0)
    assert torch.all(base_state.i_syn_ff[9] == 2.0)
    assert torch.all(base_state.i_intrinsic[9] == 2.0)
    assert torch.all(base_state.spk[9] == 2.0)

    # Test inserting a state with different dimensions
    with pytest.raises(RuntimeError):
        invalid_state = PopulationState(
            v=torch.ones((1, 1, 2, 6)),
            i_syn_local=torch.ones((1, 1, 3, 6)),
            i_syn_ff=torch.ones((1, 1, 3, 6)),
            i_intrinsic=torch.ones((1, 1, 2, 6)),
            spk=torch.ones((1, 1, 1, 6)),
        )
        base_state.insert_state(invalid_state, at_timestep=5)
