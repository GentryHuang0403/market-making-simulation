from __future__ import annotations

import os
from pathlib import Path
import tempfile

os.environ.setdefault(
    "MPLCONFIGDIR",
    str(Path(tempfile.gettempdir()) / "market_making_simulation_matplotlib"),
)

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import pandas as pd


def _prepare_output_dir(output_dir: str | Path) -> Path:
    path = Path(output_dir)
    path.mkdir(parents=True, exist_ok=True)
    return path


def plot_sample_paths(data: pd.DataFrame, output_dir: str | Path) -> list[Path]:
    """Save fair value, inventory, and PnL plots for one simulation path."""
    figure_dir = _prepare_output_dir(output_dir)
    paths: list[Path] = []

    price_path = figure_dir / "sample_fair_value_quotes.png"
    plt.figure(figsize=(10, 5))
    plt.plot(data["time_step"], data["fair_value"], label="fair value", linewidth=2)
    plt.plot(data["time_step"], data["bid_quote"], label="bid quote", alpha=0.8)
    plt.plot(data["time_step"], data["ask_quote"], label="ask quote", alpha=0.8)
    plt.xlabel("time step")
    plt.ylabel("price")
    plt.title("Fair Value and Posted Quotes")
    plt.legend()
    plt.tight_layout()
    plt.savefig(price_path)
    plt.close()
    paths.append(price_path)

    inventory_path = figure_dir / "sample_inventory_path.png"
    plt.figure(figsize=(10, 4))
    plt.plot(data["time_step"], data["inventory"], color="tab:green")
    plt.axhline(0.0, color="black", linewidth=1, alpha=0.5)
    plt.xlabel("time step")
    plt.ylabel("inventory")
    plt.title("Inventory Path")
    plt.tight_layout()
    plt.savefig(inventory_path)
    plt.close()
    paths.append(inventory_path)

    pnl_path = figure_dir / "sample_pnl_path.png"
    plt.figure(figsize=(10, 4))
    plt.plot(data["time_step"], data["total_pnl"], label="total PnL", color="tab:blue")
    plt.plot(
        data["time_step"],
        data["spread_capture"] - data["adverse_selection_cost"],
        label="spread capture minus adverse selection",
        color="tab:orange",
        alpha=0.8,
    )
    plt.xlabel("time step")
    plt.ylabel("PnL")
    plt.title("PnL Path")
    plt.legend()
    plt.tight_layout()
    plt.savefig(pnl_path)
    plt.close()
    paths.append(pnl_path)

    return paths


def plot_sweep_heatmaps(data: pd.DataFrame, output_dir: str | Path) -> list[Path]:
    """Save heatmaps for average PnL, risk-adjusted PnL, and inventory risk."""
    figure_dir = _prepare_output_dir(output_dir)
    metric_to_file = {
        "final_pnl_mean": "heatmap_average_pnl.png",
        "risk_adjusted_pnl_mean": "heatmap_risk_adjusted_pnl.png",
        "inventory_std_mean": "heatmap_inventory_volatility.png",
    }
    titles = {
        "final_pnl_mean": "Average Final PnL",
        "risk_adjusted_pnl_mean": "Risk-Adjusted PnL",
        "inventory_std_mean": "Inventory Volatility",
    }
    paths: list[Path] = []

    for metric, filename in metric_to_file.items():
        if metric not in data:
            continue
        pivot = data.pivot(
            index="inventory_penalty",
            columns="half_spread",
            values=metric,
        ).sort_index().sort_index(axis=1)

        output_path = figure_dir / filename
        plt.figure(figsize=(8, 5))
        image = plt.imshow(pivot.values, aspect="auto", origin="lower", cmap="viridis")
        plt.colorbar(image, label=metric)
        plt.xticks(range(len(pivot.columns)), [f"{value:.2f}" for value in pivot.columns])
        plt.yticks(range(len(pivot.index)), [f"{value:.3f}" for value in pivot.index])
        plt.xlabel("half-spread")
        plt.ylabel("inventory penalty")
        plt.title(titles[metric])
        plt.tight_layout()
        plt.savefig(output_path)
        plt.close()
        paths.append(output_path)

    return paths
