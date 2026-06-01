from __future__ import annotations

import math

import pandas as pd


def _last_value(data: pd.DataFrame, column: str) -> float:
    if data.empty or column not in data:
        return 0.0
    return float(data[column].iloc[-1])


def _safe_mean(series: pd.Series) -> float:
    if series.empty:
        return 0.0
    return float(series.mean())


def _safe_std(series: pd.Series) -> float:
    if series.empty:
        return 0.0
    return float(series.std(ddof=0))


def max_drawdown(pnl: pd.Series) -> float:
    """Return the largest peak-to-trough loss in a PnL path."""
    if pnl.empty:
        return 0.0
    running_peak = pnl.cummax()
    drawdown = running_peak - pnl
    return float(drawdown.max())


def compute_metrics(data: pd.DataFrame) -> dict[str, float]:
    """Compute summary statistics for a simulation DataFrame.

    The risk-adjusted PnL is Sharpe-like: average step PnL divided by step PnL
    volatility, scaled by the square root of the number of steps. It is not an
    annualized Sharpe ratio because this toy model has no calendar frequency.
    """
    if data.empty:
        return {
            "final_pnl": 0.0,
            "average_pnl": 0.0,
            "pnl_volatility": 0.0,
            "risk_adjusted_pnl": 0.0,
            "max_drawdown": 0.0,
            "fill_rate": 0.0,
            "bid_fill_rate": 0.0,
            "ask_fill_rate": 0.0,
            "average_inventory": 0.0,
            "inventory_std": 0.0,
            "max_absolute_inventory": 0.0,
            "spread_capture": 0.0,
            "adverse_selection_cost": 0.0,
            "inventory_penalty_cost": 0.0,
            "final_cash": 0.0,
            "final_mark_to_market_wealth": 0.0,
        }

    pnl = data["total_pnl"]
    step_pnl = pnl.diff().fillna(pnl.iloc[0])
    pnl_volatility = _safe_std(step_pnl)
    average_step_pnl = _safe_mean(step_pnl)
    risk_adjusted_pnl = (
        average_step_pnl / pnl_volatility * math.sqrt(len(step_pnl))
        if pnl_volatility > 0
        else 0.0
    )

    bid_fills = data["bid_fill"].astype(float)
    ask_fills = data["ask_fill"].astype(float)
    total_fill_opportunities = 2.0 * len(data)
    fill_rate = (
        float((bid_fills.sum() + ask_fills.sum()) / total_fill_opportunities)
        if total_fill_opportunities > 0
        else 0.0
    )

    return {
        "final_pnl": _last_value(data, "total_pnl"),
        "average_pnl": _safe_mean(pnl),
        "pnl_volatility": pnl_volatility,
        "risk_adjusted_pnl": float(risk_adjusted_pnl),
        "max_drawdown": max_drawdown(pnl),
        "fill_rate": fill_rate,
        "bid_fill_rate": _safe_mean(bid_fills),
        "ask_fill_rate": _safe_mean(ask_fills),
        "average_inventory": _safe_mean(data["inventory"]),
        "inventory_std": _safe_std(data["inventory"]),
        "max_absolute_inventory": float(data["inventory"].abs().max()),
        "spread_capture": _last_value(data, "spread_capture"),
        "adverse_selection_cost": _last_value(data, "adverse_selection_cost"),
        "inventory_penalty_cost": _last_value(data, "inventory_penalty_cost"),
        "final_cash": _last_value(data, "cash"),
        "final_mark_to_market_wealth": _last_value(data, "mark_to_market_wealth"),
    }
