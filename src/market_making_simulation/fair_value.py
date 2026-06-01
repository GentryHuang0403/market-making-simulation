from __future__ import annotations

from dataclasses import dataclass

import numpy as np


def _jump(
    rng: np.random.Generator,
    jump_probability: float,
    jump_std: float,
    jump_mean: float = 0.0,
) -> float:
    if jump_probability <= 0:
        return 0.0
    if rng.random() > jump_probability:
        return 0.0
    return float(rng.normal(jump_mean, jump_std))


@dataclass(frozen=True)
class GaussianRandomWalkModel:
    """Discrete-time fair value model with Gaussian shocks.

    The fair value is the unobserved economic price around which a market maker
    should quote. A random walk is a simple way to represent short-horizon price
    uncertainty without assuming the price returns to a long-run mean.
    """

    initial_value: float = 100.0
    drift: float = 0.0
    volatility: float = 0.2
    jump_probability: float = 0.0
    jump_std: float = 1.0
    jump_mean: float = 0.0
    min_value: float = 0.01

    def __post_init__(self) -> None:
        if self.initial_value <= 0:
            raise ValueError("initial_value must be positive")
        if self.volatility < 0:
            raise ValueError("volatility must be non-negative")
        if not 0 <= self.jump_probability <= 1:
            raise ValueError("jump_probability must be between 0 and 1")
        if self.jump_std < 0:
            raise ValueError("jump_std must be non-negative")
        if self.min_value <= 0:
            raise ValueError("min_value must be positive")

    def generate_path(
        self,
        steps: int,
        rng: np.random.Generator | None = None,
        seed: int | None = None,
    ) -> np.ndarray:
        """Return a fair value path with length steps + 1."""
        if steps <= 0:
            raise ValueError("steps must be positive")

        local_rng = rng or np.random.default_rng(seed)
        path = np.empty(steps + 1)
        path[0] = self.initial_value
        for step in range(1, steps + 1):
            shock = float(local_rng.normal(self.drift, self.volatility))
            jump = _jump(
                local_rng,
                self.jump_probability,
                self.jump_std,
                self.jump_mean,
            )
            path[step] = max(self.min_value, path[step - 1] + shock + jump)
        return path


@dataclass(frozen=True)
class OrnsteinUhlenbeckModel:
    """Mean-reverting fair value model.

    The Ornstein-Uhlenbeck process pulls prices back toward a long-run mean. It
    is useful for stress-testing strategies in markets where dislocations tend
    to fade rather than persist as a pure random walk.
    """

    initial_value: float = 100.0
    long_run_mean: float = 100.0
    mean_reversion: float = 0.05
    volatility: float = 0.2
    jump_probability: float = 0.0
    jump_std: float = 1.0
    jump_mean: float = 0.0
    min_value: float = 0.01

    def __post_init__(self) -> None:
        if self.initial_value <= 0:
            raise ValueError("initial_value must be positive")
        if self.long_run_mean <= 0:
            raise ValueError("long_run_mean must be positive")
        if self.mean_reversion < 0:
            raise ValueError("mean_reversion must be non-negative")
        if self.volatility < 0:
            raise ValueError("volatility must be non-negative")
        if not 0 <= self.jump_probability <= 1:
            raise ValueError("jump_probability must be between 0 and 1")
        if self.jump_std < 0:
            raise ValueError("jump_std must be non-negative")
        if self.min_value <= 0:
            raise ValueError("min_value must be positive")

    def generate_path(
        self,
        steps: int,
        rng: np.random.Generator | None = None,
        seed: int | None = None,
    ) -> np.ndarray:
        """Return a mean-reverting fair value path with length steps + 1."""
        if steps <= 0:
            raise ValueError("steps must be positive")

        local_rng = rng or np.random.default_rng(seed)
        path = np.empty(steps + 1)
        path[0] = self.initial_value
        for step in range(1, steps + 1):
            pull = self.mean_reversion * (self.long_run_mean - path[step - 1])
            shock = float(local_rng.normal(0.0, self.volatility))
            jump = _jump(
                local_rng,
                self.jump_probability,
                self.jump_std,
                self.jump_mean,
            )
            path[step] = max(self.min_value, path[step - 1] + pull + shock + jump)
        return path
