import sys
import unittest
from pathlib import Path

import numpy as np


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from market_making_simulation.experiments import run_parameter_sweep
from market_making_simulation.fair_value import GaussianRandomWalkModel
from market_making_simulation.market_maker import (
    ConstantSpreadMarketMaker,
    InventoryAwareMarketMaker,
    Quote,
)
from market_making_simulation.metrics import compute_metrics
from market_making_simulation.simulator import (
    MarketMakingSimulator,
    SimulationConfig,
    apply_fills,
)


class MarketMakingProjectTest(unittest.TestCase):
    def test_fair_value_process_is_reproducible_with_fixed_seed(self) -> None:
        model = GaussianRandomWalkModel(initial_value=100.0, volatility=0.2)

        first_path = model.generate_path(steps=5, seed=123)
        second_path = model.generate_path(steps=5, seed=123)

        np.testing.assert_allclose(first_path, second_path)

    def test_market_maker_quotes_have_bid_below_ask(self) -> None:
        constant = ConstantSpreadMarketMaker(half_spread=0.5)
        inventory_aware = InventoryAwareMarketMaker(
            half_spread=0.5,
            inventory_penalty=0.05,
        )

        constant_quote = constant.quote(fair_value=100.0)
        inventory_quote = inventory_aware.quote(fair_value=100.0, inventory=10.0)

        self.assertLess(constant_quote.bid_price, constant_quote.ask_price)
        self.assertLess(inventory_quote.bid_price, inventory_quote.ask_price)

    def test_inventory_and_cash_update_after_bid_and_ask_fills(self) -> None:
        quote = Quote(bid_price=99.0, ask_price=101.0, bid_size=2.0, ask_size=1.0)

        after_bid = apply_fills(
            inventory=0.0,
            cash=0.0,
            quote=quote,
            fair_value=100.0,
            bid_filled=True,
            ask_filled=False,
        )
        after_ask = apply_fills(
            inventory=after_bid.inventory,
            cash=after_bid.cash,
            quote=quote,
            fair_value=100.0,
            bid_filled=False,
            ask_filled=True,
        )

        self.assertEqual(after_bid.inventory, 2.0)
        self.assertEqual(after_bid.cash, -198.0)
        self.assertEqual(after_ask.inventory, 1.0)
        self.assertEqual(after_ask.cash, -97.0)

    def test_simulation_returns_required_columns(self) -> None:
        simulator = MarketMakingSimulator(
            strategy=InventoryAwareMarketMaker(half_spread=0.5, inventory_penalty=0.02),
            config=SimulationConfig(steps=20, seed=7),
        )

        data = simulator.run()

        required_columns = {
            "time_step",
            "fair_value",
            "mid_price",
            "bid_quote",
            "ask_quote",
            "bid_fill",
            "ask_fill",
            "inventory",
            "cash",
            "cash_ledger",
            "cash_pnl",
            "mark_to_market_wealth",
            "realized_pnl",
            "unrealized_pnl",
            "total_pnl",
            "spread_capture",
            "adverse_selection_cost",
            "inventory_penalty_cost",
        }
        self.assertFalse(data.empty)
        self.assertTrue(required_columns.issubset(data.columns))

    def test_metrics_contain_required_keys(self) -> None:
        data = MarketMakingSimulator(config=SimulationConfig(steps=20, seed=8)).run()

        metrics = compute_metrics(data)

        required_keys = {
            "final_pnl",
            "average_pnl",
            "pnl_volatility",
            "risk_adjusted_pnl",
            "max_drawdown",
            "fill_rate",
            "bid_fill_rate",
            "ask_fill_rate",
            "average_inventory",
            "inventory_std",
            "max_absolute_inventory",
            "spread_capture",
            "adverse_selection_cost",
            "final_cash",
            "final_cash_pnl",
            "final_mark_to_market_wealth",
        }
        self.assertTrue(required_keys.issubset(metrics))

    def test_realized_pnl_is_cash_pnl_compatibility_alias(self) -> None:
        data = MarketMakingSimulator(config=SimulationConfig(steps=20, seed=9)).run()

        np.testing.assert_allclose(data["realized_pnl"], data["cash_pnl"])

    def test_parameter_sweep_returns_non_empty_aggregated_results(self) -> None:
        results = run_parameter_sweep(
            half_spreads=[0.25, 0.50],
            inventory_penalties=[0.0, 0.02],
            seeds=[1, 2],
            steps=15,
        )

        self.assertFalse(results.empty)
        self.assertEqual(len(results), 4)
        self.assertIn("final_pnl_mean", results.columns)
        self.assertIn("risk_adjusted_pnl_mean", results.columns)


if __name__ == "__main__":
    unittest.main()
