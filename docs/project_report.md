# Market Making Simulation Project Report

## Problem Statement

The goal is to simulate a simple electronic market-making game. A market maker observes a stochastic fair value, posts bid and ask quotes, receives random market order flow, tracks inventory and cash, and evaluates PnL. The project is designed to support experiments over spread width and inventory penalty so the trade-off between fill rate, adverse selection, inventory risk, and PnL can be studied.

## Model Design

The simulation runs in discrete time. At each step:

1. The market maker observes the current fair value.
2. The strategy posts bid and ask quotes.
3. The fair value model generates the next fair value.
4. The order-flow model draws bid and ask fills using quote distance and adverse-selection direction.
5. Inventory, cash, mark-to-market wealth, and PnL attribution are recorded.

The output of a run is a pandas DataFrame with one row per time step.

## Stochastic Fair Value

The default fair value model is a Gaussian random walk:

```text
fair_value[t + 1] = fair_value[t] + drift + gaussian_shock + optional_jump
```

This keeps the model easy to understand while still creating price risk. The package also includes an Ornstein-Uhlenbeck model for mean-reverting fair values:

```text
fair_value[t + 1] = fair_value[t] + kappa * (long_run_mean - fair_value[t]) + shock
```

Both models accept explicit seeds for reproducibility. The optional jump component is included to create occasional larger moves that can stress inventory and adverse-selection assumptions.

## Order Arrivals

The order-flow model uses a Poisson-style fill probability:

```text
fill_probability = 1 - exp(-base_intensity * exp(-distance_decay * quote_distance))
```

Tighter quotes have lower quote distance and therefore higher fill probability. Wider quotes are less likely to trade. The model adds adverse selection by increasing ask-fill probability before upward fair value moves and bid-fill probability before downward fair value moves. This reflects the idea that market makers are more likely to sell before prices rise or buy before prices fall.

## Inventory-Aware Quoting

Two strategies are implemented.

The constant-spread strategy always quotes:

```text
bid = fair_value - half_spread
ask = fair_value + half_spread
```

The inventory-aware strategy uses a simple reservation price:

```text
reservation_price = fair_value - inventory_penalty * inventory
```

Positive inventory lowers the reservation price, lowering the ask and encouraging sales. Negative inventory raises the reservation price, raising the bid and encouraging purchases. This is inspired by Avellaneda-Stoikov intuition, but intentionally avoids the full stochastic-control derivation.

## PnL Attribution

The simulator records:

- cash from executed trades
- inventory valued at fair value
- mark-to-market wealth
- realized PnL as the cash ledger relative to initial cash
- unrealized PnL as inventory marked to fair value
- total PnL as mark-to-market wealth relative to initial wealth
- spread capture versus current fair value
- adverse selection cost versus next fair value
- inventory penalty cost as a quadratic diagnostic

The realized/unrealized split is simple and educational. It is not a tax-lot or FIFO accounting system.

## Parameter Sweep Methodology

The default sweep runs 500-step simulations across:

- half-spreads: `0.20`, `0.40`, `0.60`, `0.80`, `1.00`
- inventory penalties: `0.00`, `0.01`, `0.03`, `0.05`
- random seeds: `1`, `2`, `3`, `4`, `5`

For each parameter combination, the project computes metrics for each seed and then aggregates means and standard deviations into `outputs/sweep_results.csv`.

## Generated Results Summary

The generated sample run with seed 42 and 500 steps ended with final PnL of about `66.7891` and fill rate of about `0.1720`.

In the generated default sweep, the highest average final PnL occurred at half-spread `0.80` and inventory penalty `0.00`, with average final PnL around `95.7979`. The highest average risk-adjusted PnL occurred at half-spread `0.80` and inventory penalty `0.05`, with risk-adjusted PnL around `6.7529` and lower inventory volatility than the zero-penalty case. This suggests the inventory-aware strategy can trade some raw PnL for smoother inventory and PnL behavior in this simulated setup.

These results are generated from the included toy model and should not be interpreted as evidence about real trading profitability.

## Expected Qualitative Findings

Wider spreads usually reduce fill rates but can increase spread capture per fill. Very tight spreads trade more often but are more exposed to adverse selection. Inventory penalties tend to reduce inventory volatility and maximum inventory, but high penalties can make quotes less competitive and may reduce raw PnL. Risk-adjusted PnL can therefore prefer a different parameter setting than final PnL.

## Limitations

The model is deliberately simplified. It does not include queue priority, latency, exchange fees, partial fills, cancellations, multiple venues, real calibration, or a real alpha signal. Adverse selection is based on the next simulated fair value move, which is useful for testing but not directly observable in live trading. Future extensions could add calibrated market order intensities, fees and rebates, queue position, latency, multiple assets, and strategy comparison against real historical data.
