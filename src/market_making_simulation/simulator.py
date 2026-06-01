from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

import numpy as np
import pandas as pd

from .fair_value import GaussianRandomWalkModel, OrnsteinUhlenbeckModel
from .market_maker import ConstantSpreadMarketMaker, Quote
from .order_flow import FillResult, OrderFlowModel


class MarketMakingStrategy(Protocol):
    """Interface used by the simulator for quoting strategies."""

    name: str
    inventory_penalty: float

    def quote(self, fair_value: float, inventory: float = 0.0) -> Quote:
        """Return bid and ask quotes for the current fair value."""


@dataclass(frozen=True)
class SimulationConfig:
    """Configuration for a single market-making simulation run."""

    steps: int = 500
    initial_fair_value: float = 100.0
    fair_value_model: str = "random_walk"
    drift: float = 0.0
    volatility: float = 0.2
    long_run_mean: float = 100.0
    mean_reversion: float = 0.05
    jump_probability: float = 0.01
    jump_std: float = 0.75
    order_size: float = 1.0
    initial_inventory: float = 0.0
    initial_cash: float = 0.0
    seed: int = 42

    def __post_init__(self) -> None:
        if self.steps <= 0:
            raise ValueError("steps must be positive")
        if self.initial_fair_value <= 0:
            raise ValueError("initial_fair_value must be positive")
        if self.volatility < 0:
            raise ValueError("volatility must be non-negative")
        if self.order_size <= 0:
            raise ValueError("order_size must be positive")


@dataclass(frozen=True)
class TradeUpdate:
    """Inventory, cash, and attribution update from bid and ask fills."""

    inventory: float
    cash: float
    spread_capture: float


def build_fair_value_model(
    config: SimulationConfig,
) -> GaussianRandomWalkModel | OrnsteinUhlenbeckModel:
    """Create the fair value process requested by the simulation config."""
    if config.fair_value_model == "random_walk":
        return GaussianRandomWalkModel(
            initial_value=config.initial_fair_value,
            drift=config.drift,
            volatility=config.volatility,
            jump_probability=config.jump_probability,
            jump_std=config.jump_std,
        )
    if config.fair_value_model == "ou":
        return OrnsteinUhlenbeckModel(
            initial_value=config.initial_fair_value,
            long_run_mean=config.long_run_mean,
            mean_reversion=config.mean_reversion,
            volatility=config.volatility,
            jump_probability=config.jump_probability,
            jump_std=config.jump_std,
        )
    raise ValueError("fair_value_model must be 'random_walk' or 'ou'")


def apply_fills(
    inventory: float,
    cash: float,
    quote: Quote,
    fair_value: float,
    bid_filled: bool,
    ask_filled: bool,
) -> TradeUpdate:
    """Apply bid/ask fills to inventory and cash.

    A bid fill means the market maker buys at the bid, increasing inventory and
    reducing cash. An ask fill means the market maker sells at the ask, reducing
    inventory and increasing cash.
    """
    updated_inventory = inventory
    updated_cash = cash
    spread_capture = 0.0

    if bid_filled:
        updated_inventory += quote.bid_size
        updated_cash -= quote.bid_price * quote.bid_size
        spread_capture += max(0.0, fair_value - quote.bid_price) * quote.bid_size
    if ask_filled:
        updated_inventory -= quote.ask_size
        updated_cash += quote.ask_price * quote.ask_size
        spread_capture += max(0.0, quote.ask_price - fair_value) * quote.ask_size

    return TradeUpdate(
        inventory=updated_inventory,
        cash=updated_cash,
        spread_capture=spread_capture,
    )


def adverse_selection_cost(
    quote: Quote,
    next_fair_value: float,
    bid_filled: bool,
    ask_filled: bool,
) -> float:
    """Measure loss from being filled before the fair value moves against us."""
    cost = 0.0
    if bid_filled:
        cost += max(0.0, quote.bid_price - next_fair_value) * quote.bid_size
    if ask_filled:
        cost += max(0.0, next_fair_value - quote.ask_price) * quote.ask_size
    return cost


class MarketMakingSimulator:
    """Discrete-time simulator for a simple electronic market-making game."""

    def __init__(
        self,
        strategy: MarketMakingStrategy | None = None,
        config: SimulationConfig | None = None,
        order_flow: OrderFlowModel | None = None,
    ) -> None:
        self.config = config or SimulationConfig()
        self.strategy = strategy or ConstantSpreadMarketMaker(
            quote_size=self.config.order_size
        )
        self.order_flow = order_flow or OrderFlowModel()

    def run(self) -> pd.DataFrame:
        """Run the simulation and return a row-per-step pandas DataFrame."""
        rng = np.random.default_rng(self.config.seed)
        fair_value_model = build_fair_value_model(self.config)
        fair_values = fair_value_model.generate_path(self.config.steps, rng=rng)

        inventory = self.config.initial_inventory
        cash = self.config.initial_cash
        initial_wealth = cash + inventory * fair_values[0]
        cumulative_spread_capture = 0.0
        cumulative_adverse_selection_cost = 0.0
        cumulative_inventory_penalty_cost = 0.0
        records: list[dict[str, float | int | bool | str]] = []

        for step in range(self.config.steps):
            current_fair_value = float(fair_values[step])
            next_fair_value = float(fair_values[step + 1])
            quote = self.strategy.quote(current_fair_value, inventory=inventory)
            fill_result = self.order_flow.simulate_fills(
                bid_price=quote.bid_price,
                ask_price=quote.ask_price,
                current_fair_value=current_fair_value,
                next_fair_value=next_fair_value,
                rng=rng,
            )

            trade_update = apply_fills(
                inventory=inventory,
                cash=cash,
                quote=quote,
                fair_value=current_fair_value,
                bid_filled=fill_result.bid_filled,
                ask_filled=fill_result.ask_filled,
            )
            inventory = trade_update.inventory
            cash = trade_update.cash

            step_adverse_selection_cost = adverse_selection_cost(
                quote=quote,
                next_fair_value=next_fair_value,
                bid_filled=fill_result.bid_filled,
                ask_filled=fill_result.ask_filled,
            )
            penalty_rate = getattr(self.strategy, "inventory_penalty", 0.0)
            step_inventory_penalty_cost = penalty_rate * inventory * inventory

            cumulative_spread_capture += trade_update.spread_capture
            cumulative_adverse_selection_cost += step_adverse_selection_cost
            cumulative_inventory_penalty_cost += step_inventory_penalty_cost

            wealth = cash + inventory * next_fair_value
            realized_pnl = cash - self.config.initial_cash
            unrealized_pnl = inventory * next_fair_value - (
                self.config.initial_inventory * fair_values[0]
            )
            total_pnl = wealth - initial_wealth

            records.append(
                {
                    "time_step": step + 1,
                    "fair_value": next_fair_value,
                    "mid_price": next_fair_value,
                    "quote_reference": current_fair_value,
                    "bid_quote": quote.bid_price,
                    "ask_quote": quote.ask_price,
                    "bid_fill": fill_result.bid_filled,
                    "ask_fill": fill_result.ask_filled,
                    "bid_fill_probability": fill_result.bid_probability,
                    "ask_fill_probability": fill_result.ask_probability,
                    "bid_trade_size": quote.bid_size if fill_result.bid_filled else 0.0,
                    "ask_trade_size": quote.ask_size if fill_result.ask_filled else 0.0,
                    "inventory": inventory,
                    "cash": cash,
                    "mark_to_market_wealth": wealth,
                    "realized_pnl": realized_pnl,
                    "unrealized_pnl": unrealized_pnl,
                    "total_pnl": total_pnl,
                    "step_spread_capture": trade_update.spread_capture,
                    "spread_capture": cumulative_spread_capture,
                    "step_adverse_selection_cost": step_adverse_selection_cost,
                    "adverse_selection_cost": cumulative_adverse_selection_cost,
                    "step_inventory_penalty_cost": step_inventory_penalty_cost,
                    "inventory_penalty_cost": cumulative_inventory_penalty_cost,
                    "strategy": self.strategy.name,
                }
            )

        return pd.DataFrame.from_records(records)
