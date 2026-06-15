from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import random
import sys

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    from market_making_simulation.market_maker import MarketMaker
else:
    from .market_maker import MarketMaker


@dataclass(frozen=True)
class SimulationRecord:
    step: int
    inventory: float
    cash: float
    mid_price: float
    pnl: float
    bid_price: float
    ask_price: float


def run_simulation(
    steps: int,
    initial_mid_price: float = 100.0,
    price_tick: float = 0.1,
    maker: MarketMaker | None = None,
    seed: int | None = None,
) -> list[SimulationRecord]:
    """Run a tiny market-making simulation over a mid-price random walk."""
    if steps <= 0:
        raise ValueError("steps must be positive")
    if initial_mid_price <= 0:
        raise ValueError("initial_mid_price must be positive")
    if price_tick <= 0:
        raise ValueError("price_tick must be positive")

    market_maker = maker or MarketMaker()
    rng = random.Random(seed)
    mid_price = initial_mid_price
    inventory = 0.0
    cash = 0.0
    records: list[SimulationRecord] = []

    for step in range(1, steps + 1):
        direction = rng.choice((-1.0, 1.0))
        mid_price = max(price_tick, mid_price + direction * price_tick)
        quote = market_maker.quote(mid_price)

        if direction > 0:
            inventory -= quote.ask_size
            cash += quote.ask_price * quote.ask_size
        else:
            inventory += quote.bid_size
            cash -= quote.bid_price * quote.bid_size

        pnl = cash + inventory * mid_price
        records.append(
            SimulationRecord(
                step=step,
                inventory=inventory,
                cash=cash,
                mid_price=mid_price,
                pnl=pnl,
                bid_price=quote.bid_price,
                ask_price=quote.ask_price,
            )
        )

    return records


def main() -> None:
    for record in run_simulation(steps=10, seed=1):
        print(
            f"step={record.step} "
            f"mid={record.mid_price:.2f} "
            f"bid={record.bid_price:.2f} "
            f"ask={record.ask_price:.2f} "
            f"inventory={record.inventory:.2f} "
            f"cash={record.cash:.2f} "
            f"pnl={record.pnl:.2f}"
        )


if __name__ == "__main__":
    main()
