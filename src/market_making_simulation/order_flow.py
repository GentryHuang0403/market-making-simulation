from __future__ import annotations

from dataclasses import dataclass
import math

import numpy as np


@dataclass(frozen=True)
class FillResult:
    """Random fill outcome for the market maker's bid and ask quotes."""

    bid_filled: bool
    ask_filled: bool
    bid_probability: float
    ask_probability: float


@dataclass(frozen=True)
class OrderFlowModel:
    """Poisson-style order arrival model driven by quote distance.

    Quote distance is the difference between fair value and the posted quote.
    Tight quotes have small distance and therefore higher fill probability.
    Adverse selection is modeled by increasing ask-fill probability before an
    upward fair value move and increasing bid-fill probability before a downward
    fair value move.
    """

    base_intensity: float = 0.30
    distance_decay: float = 1.50
    adverse_selection_strength: float = 0.75
    max_fill_probability: float = 0.95

    def __post_init__(self) -> None:
        if self.base_intensity < 0:
            raise ValueError("base_intensity must be non-negative")
        if self.distance_decay < 0:
            raise ValueError("distance_decay must be non-negative")
        if self.adverse_selection_strength < 0:
            raise ValueError("adverse_selection_strength must be non-negative")
        if not 0 <= self.max_fill_probability <= 1:
            raise ValueError("max_fill_probability must be between 0 and 1")

    def fill_probability(self, distance: float, adverse: bool = False) -> float:
        """Convert quote distance into a fill probability for one time step."""
        adjusted_distance = max(0.0, distance)
        intensity = self.base_intensity * math.exp(-self.distance_decay * adjusted_distance)
        if adverse:
            intensity *= 1.0 + self.adverse_selection_strength
        probability = 1.0 - math.exp(-intensity)
        return min(self.max_fill_probability, max(0.0, probability))

    def simulate_fills(
        self,
        bid_price: float,
        ask_price: float,
        current_fair_value: float,
        next_fair_value: float,
        rng: np.random.Generator,
    ) -> FillResult:
        """Draw bid and ask fills for one step of the simulation."""
        bid_distance = current_fair_value - bid_price
        ask_distance = ask_price - current_fair_value
        fair_value_move = next_fair_value - current_fair_value

        bid_probability = self.fill_probability(
            bid_distance,
            adverse=fair_value_move < 0,
        )
        ask_probability = self.fill_probability(
            ask_distance,
            adverse=fair_value_move > 0,
        )

        return FillResult(
            bid_filled=bool(rng.random() < bid_probability),
            ask_filled=bool(rng.random() < ask_probability),
            bid_probability=bid_probability,
            ask_probability=ask_probability,
        )
