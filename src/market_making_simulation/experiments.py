from __future__ import annotations

from pathlib import Path
from collections.abc import Sequence

import pandas as pd

from .market_maker import ConstantSpreadMarketMaker, InventoryAwareMarketMaker
from .metrics import compute_metrics
from .plotting import plot_sample_paths, plot_sweep_heatmaps
from .simulator import MarketMakingSimulator, SimulationConfig


DEFAULT_HALF_SPREADS = [0.20, 0.40, 0.60, 0.80, 1.00]
DEFAULT_INVENTORY_PENALTIES = [0.00, 0.01, 0.03, 0.05]
DEFAULT_SEEDS = [1, 2, 3, 4, 5]


def run_sample_simulation(
    steps: int = 500,
    seed: int = 42,
    half_spread: float = 0.50,
    inventory_penalty: float = 0.03,
) -> pd.DataFrame:
    """Run one representative inventory-aware market-making simulation."""
    strategy = InventoryAwareMarketMaker(
        half_spread=half_spread,
        quote_size=1.0,
        inventory_penalty=inventory_penalty,
    )
    config = SimulationConfig(steps=steps, seed=seed)
    return MarketMakingSimulator(strategy=strategy, config=config).run()


def run_parameter_sweep(
    half_spreads: Sequence[float] | None = None,
    inventory_penalties: Sequence[float] | None = None,
    seeds: Sequence[int] | None = None,
    steps: int = 500,
) -> pd.DataFrame:
    """Run simulations over spread, inventory penalty, and random seed values."""
    spread_values = list(half_spreads or DEFAULT_HALF_SPREADS)
    penalty_values = list(inventory_penalties or DEFAULT_INVENTORY_PENALTIES)
    seed_values = list(seeds or DEFAULT_SEEDS)

    run_rows: list[dict[str, float | int | str]] = []
    for half_spread in spread_values:
        for inventory_penalty in penalty_values:
            for seed in seed_values:
                if inventory_penalty == 0:
                    strategy = ConstantSpreadMarketMaker(half_spread=half_spread)
                else:
                    strategy = InventoryAwareMarketMaker(
                        half_spread=half_spread,
                        inventory_penalty=inventory_penalty,
                    )
                config = SimulationConfig(steps=steps, seed=seed)
                path = MarketMakingSimulator(strategy=strategy, config=config).run()
                metrics = compute_metrics(path)
                run_rows.append(
                    {
                        "half_spread": half_spread,
                        "inventory_penalty": inventory_penalty,
                        "seed": seed,
                        "strategy": strategy.name,
                        **metrics,
                    }
                )

    run_data = pd.DataFrame(run_rows)
    if run_data.empty:
        return run_data

    metric_columns = [
        column
        for column in run_data.columns
        if column not in {"half_spread", "inventory_penalty", "seed", "strategy"}
    ]
    aggregated = (
        run_data.groupby(["half_spread", "inventory_penalty"])[metric_columns]
        .agg(["mean", "std"])
        .reset_index()
    )
    aggregated.columns = [
        "_".join(part for part in column if part)
        if isinstance(column, tuple)
        else column
        for column in aggregated.columns
    ]
    aggregated = aggregated.fillna(0.0)
    aggregated["n_runs"] = len(seed_values)
    return aggregated


def save_sample_outputs(data: pd.DataFrame, output_dir: str | Path = "outputs") -> None:
    """Save one simulation path and its sample plots."""
    path = Path(output_dir)
    figure_dir = path / "figures"
    path.mkdir(parents=True, exist_ok=True)
    data.to_csv(path / "sample_path.csv", index=False)
    plot_sample_paths(data, figure_dir)


def save_sweep_outputs(data: pd.DataFrame, output_dir: str | Path = "outputs") -> None:
    """Save aggregated sweep results and heatmap plots."""
    path = Path(output_dir)
    figure_dir = path / "figures"
    path.mkdir(parents=True, exist_ok=True)
    data.to_csv(path / "sweep_results.csv", index=False)
    plot_sweep_heatmaps(data, figure_dir)


def run_default_outputs(output_dir: str | Path = "outputs") -> tuple[pd.DataFrame, pd.DataFrame]:
    """Run the default sample and sweep, saving CSVs and figures."""
    sample = run_sample_simulation()
    save_sample_outputs(sample, output_dir)
    sweep = run_parameter_sweep()
    save_sweep_outputs(sweep, output_dir)
    return sample, sweep
