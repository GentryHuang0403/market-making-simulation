# Market Making Simulation

Market Making Simulation is a Python 3.12 project for studying a simple electronic market-making game. It models stochastic fair value, bid/ask quoting, random order arrivals, inventory, cash, mark-to-market PnL, spread capture, adverse selection, and inventory-aware quoting.

The project is intentionally compact enough to read in an interview, but it runs real simulations and parameter sweeps rather than only providing boilerplate.

## Financial Intuition

A market maker posts a bid and an ask around an estimated fair value. If a sell market order hits the bid, the market maker buys and inventory increases. If a buy market order lifts the ask, the market maker sells and inventory decreases.

The market maker earns spread capture when trades happen at favorable prices around fair value. The risk is that fills are not random in a harmless way: informed or adverse flow is more likely before the fair value moves against the market maker. Inventory also creates risk because mark-to-market PnL changes as fair value moves.

## Model Assumptions

- Fair value evolves in discrete time.
- The default fair value process is a Gaussian random walk with optional jumps.
- An Ornstein-Uhlenbeck mean-reverting model is also available.
- Fill probability decreases as quotes move farther from fair value.
- Ask fills become more likely before upward fair value moves.
- Bid fills become more likely before downward fair value moves.
- The inventory-aware strategy shifts its reservation price by `inventory_penalty * inventory`.
- PnL is marked to the simulated fair value at every step.

## Project Layout

```text
src/market_making_simulation/
    fair_value.py
    order_flow.py
    market_maker.py
    simulator.py
    metrics.py
    experiments.py
    plotting.py
    cli.py
    simulation.py
tests/
docs/project_report.md
outputs/
```

## Environment

Use Python 3.12 and the local virtual environment:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

No new third-party dependencies are required beyond the standard library plus numpy, pandas, scipy, and matplotlib already listed in the environment.

Because this repository uses a `src/` layout, either install the project in editable mode:

```powershell
.\.venv\Scripts\python.exe -m pip install -e .
```

or set `PYTHONPATH` for the current PowerShell session:

```powershell
$env:PYTHONPATH = "src"
```

## Running Tests

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests
```

## Running Simulations

Sample path:

```powershell
$env:PYTHONPATH = "src"
.\.venv\Scripts\python.exe -m market_making_simulation.cli --mode sample
```

Parameter sweep:

```powershell
$env:PYTHONPATH = "src"
.\.venv\Scripts\python.exe -m market_making_simulation.cli --mode sweep
```

Run both:

```powershell
$env:PYTHONPATH = "src"
.\.venv\Scripts\python.exe -m market_making_simulation.cli --mode all
```

## Output Files

The default commands write:

- `outputs/sample_path.csv`: row-by-row path for one representative simulation.
- `outputs/sweep_results.csv`: aggregated metrics over half-spread, inventory penalty, and random seed.
- `outputs/figures/sample_fair_value_quotes.png`: fair value, bid, and ask path.
- `outputs/figures/sample_inventory_path.png`: inventory over time.
- `outputs/figures/sample_pnl_path.png`: total PnL path.
- `outputs/figures/heatmap_average_pnl.png`: average final PnL grid.
- `outputs/figures/heatmap_risk_adjusted_pnl.png`: risk-adjusted PnL grid.
- `outputs/figures/heatmap_inventory_volatility.png`: inventory volatility grid.

## Metrics

- `final_pnl`: ending mark-to-market PnL.
- `average_pnl`: average total PnL over the path.
- `pnl_volatility`: standard deviation of step PnL changes.
- `risk_adjusted_pnl`: Sharpe-like score using average step PnL divided by step PnL volatility.
- `max_drawdown`: largest peak-to-trough PnL loss.
- `fill_rate`: fraction of bid/ask quote opportunities that filled.
- `bid_fill_rate` and `ask_fill_rate`: side-specific fill rates.
- `average_inventory`, `inventory_std`, `max_absolute_inventory`: inventory risk measures.
- `spread_capture`: cumulative quoted spread earned against fair value.
- `adverse_selection_cost`: cumulative cost from being filled before fair value moves against the trade.
- `inventory_penalty_cost`: cumulative quadratic inventory penalty used for diagnostics.
- `final_cash`: ending cash ledger.
- `final_mark_to_market_wealth`: cash plus inventory valued at fair value.

## Generated Baseline Results

Using the default sample run with seed 42 and 500 steps, the generated sample path ended with final PnL of about `66.7891` and fill rate of about `0.1720`.

The default sweep uses half-spreads `[0.20, 0.40, 0.60, 0.80, 1.00]`, inventory penalties `[0.00, 0.01, 0.03, 0.05]`, five random seeds, and 500 steps per run. In the generated sweep, the highest average final PnL occurred at half-spread `0.80` with inventory penalty `0.00`; the highest risk-adjusted PnL occurred at half-spread `0.80` with inventory penalty `0.05`. This is consistent with the intuition that inventory-aware quoting can reduce inventory volatility while sometimes giving up some raw PnL.

## Limitations

This is an educational simulation, not a production trading system. It does not model queue position, latency, exchange fees, hidden liquidity, order cancellations, multi-asset risk, calibrated order flow, or real market microstructure data. Useful extensions would include calibrated intensities, transaction costs, latency, queue priority, alternative strategies, and richer adverse-selection models.
