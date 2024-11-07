import torch
from lab.model.network.dendrites import Dendrite
from lab.model.spec.network import DendriteSpec, Dale


def test_dendrite_current():
    # Test basic functionality
    weights = torch.tensor([[1.0, 2.0], [3.0, 4.0]])
    signal = torch.tensor([1.0, 2.0])

    dendrite = Dendrite(weights=weights, tau=50)
    dendrite = dendrite.with_signal(signal)

    expected_current = torch.tensor([7.0, 10.0])
    assert torch.allclose(dendrite.current, expected_current)


def test_dendrite_parity():
    # Test parity
    weights = torch.tensor([[1.0, 2.0], [3.0, 4.0]])
    signal = torch.tensor([1.0, 2.0])

    # Positive parity (default)
    dendrite_pos = Dendrite(weights=weights, tau=50)
    dendrite_pos = dendrite_pos.with_signal(signal)

    # Negative parity
    dendrite_neg = Dendrite(weights=weights, tau=50, parity=-1)
    dendrite_neg = dendrite_neg.with_signal(signal)

    assert torch.allclose(dendrite_pos.current, -dendrite_neg.current)


def test_dendrite_density_mask():
    shape = (20, 20)
    spec = DendriteSpec(shape=shape, init=(10.0, 0.01), density=0.5)
    dendrite = spec.build()

    # Check if approximately half of the weights are zero
    zero_count = torch.sum(dendrite.weights == 0).item()
    assert 150 <= zero_count <= 250  # Allow some flexibility due to randomness

    # Check if gradients are masked
    signal = torch.rand(20)  # Random signal matching the input dimension
    dendrite = dendrite.with_signal(signal)

    dendrite.current.sum().backward()

    assert dendrite.weights.grad is not None

    # Check if gradients are zero where weights are zero
    assert torch.allclose(
        dendrite.weights.grad[dendrite.weights == 0], torch.tensor(0.0)
    )

    # Check if non-zero weights have non-zero gradients
    assert torch.any(dendrite.weights.grad[dendrite.weights != 0] != 0)


def test_dendrite_dale():
    # Test Dale's law
    shape = (2, 2)
    spec = DendriteSpec(shape=shape, init=(0.0, 1.0), dale=Dale.EXC, train=True)
    dendrite = spec.build()

    # Check if all weights are non-negative
    assert torch.all(dendrite.weights >= 0)

    # Test if weights remain non-negative after update
    signal = torch.tensor([1.0, 2.0])
    dendrite = dendrite.with_signal(signal)

    # Compute a loss and perform backward pass
    loss = dendrite.current.sum()
    loss.backward()

    assert dendrite.weights.grad is not None

    # Simulate a weight update
    with torch.no_grad():
        dendrite.weights -= 0.1 * dendrite.weights.grad

    dendrite.ensure_conditions()

    # Check if weights are still non-negative
    assert torch.all(dendrite.weights >= 0)
