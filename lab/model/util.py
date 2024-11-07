from typing import Any, Self
import torch

from lab.model import Model

milli = 0.001


class Vary(Model):
    param: str
    lower: float
    upper: float
    count: int

    @property
    def values(self) -> torch.Tensor:
        return torch.linspace(self.lower, self.upper, self.count)

    @classmethod
    def parse_str(cls, vary: str) -> Self:
        """Parse a Vary string

        e.g.    --vary freq:1:50:10

        """
        parts = vary.split(":")
        if len(parts) != 4:
            raise ValueError(
                "Invalid vary string format. Expected <hyper>:<lower>:<upper>:<count>"
            )

        param, lower_str, upper_str, count_str = parts

        try:
            lower = float(lower_str)
            upper = float(upper_str)
            count = int(count_str)
        except ValueError:
            raise ValueError("Invalid numeric values in vary string")

        return cls(param=param, lower=lower, upper=upper, count=count)


class SuperSpike(torch.autograd.Function):
    r"""SuperSpike surrogate gradient as described in Section 3.3.2 of

    F. Zenke, S. Ganguli, "SuperSpike: Supervised Learning in Multilayer Spiking Neural
        Networks",
    Neural Computation 30, 1514–1541 (2018),
    `doi:10.1162/neco_a_01086 <https://www.mitpressjournals.org/doi/full/10.1162/neco_a_01086>`_
    """

    @staticmethod
    def forward(ctx, input_tensor: torch.Tensor, alpha: float) -> torch.Tensor:
        ctx.save_for_backward(input_tensor)
        ctx.alpha = alpha
        return torch.gt(input_tensor, torch.as_tensor(0.0)).to(
            input_tensor.dtype
        )  # pragma: no cover

    @staticmethod
    def backward(ctx: Any, *grad_outputs: torch.Tensor) -> Any:
        (inp,) = ctx.saved_tensors
        assert isinstance(grad_outputs, tuple)
        (grad_output,) = grad_outputs
        alpha = ctx.alpha
        grad_input = grad_output.clone()
        grad = grad_input / (alpha * torch.abs(inp) + 1.0).pow(2)
        return grad, None
