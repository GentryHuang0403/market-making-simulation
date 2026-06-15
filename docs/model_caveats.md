# Model Caveats

This project is intentionally a toy simulator. It is useful for practicing a market-making research workflow, but it should not be described as a real trading system, a production backtest, or evidence of a tradable edge.

## Order Flow Is Not Calibrated

The order-flow model uses a hand-specified Poisson-style intensity function. It is not estimated from real tick data, exchange messages, or limit order book data. In a production research setting, order-arrival intensity would need to be calibrated from market data and stress-tested across assets, regimes, and venues.

## Adverse Selection Uses Simulated Future Movement

The simulator uses `next_fair_value` to make ask fills more likely before upward simulated fair-value moves and bid fills more likely before downward simulated fair-value moves. This is a data-generating mechanism for creating informed-flow-like behavior inside the simulator.

The quoting strategy does not observe `next_fair_value`. This is not a strategy using future information. In live trading, the next fair value is not known in advance.

## No Queue Position

The model treats a quote fill as a random event based on quote distance and simulated adverse-selection direction. Real market making is more constrained: posting a bid or ask does not mean the order will trade. Queue position, quantity ahead, cancellations, partial fills, message latency, and exchange matching rules all matter.

## No Fees Or Rebates

The model does not include exchange fees, rebates, or other transaction costs. This is a major simplification because market-making margins can be thin, and fees or rebates can materially change strategy ranking.

## Simplified PnL Accounting

The simulator tracks cash and mark-to-market wealth. The `cash_ledger` column records the cash account, and `total_pnl` is cash plus inventory marked to fair value relative to initial wealth.

The `realized_pnl` column is kept as a compatibility alias for `cash_pnl`, not as strict accounting realized PnL. A rigorous realized PnL calculation would require lot-level accounting such as FIFO, LIFO, or average cost.

Safer interview phrasing:

> I track cash and mark-to-market wealth. The realized/unrealized split is simplified; the main PnL measure is cash plus inventory marked to fair value.
