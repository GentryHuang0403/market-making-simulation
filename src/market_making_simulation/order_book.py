from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class BookLevel:
    price: float
    quantity: float


class LimitOrderBook:
    """Minimal price-level limit order book for simulation smoke tests."""

    def __init__(self) -> None:
        self._bids: dict[float, float] = {}
        self._asks: dict[float, float] = {}

    def add_limit_order(self, side: str, price: float, quantity: float) -> None:
        if price <= 0:
            raise ValueError("price must be positive")
        if quantity <= 0:
            raise ValueError("quantity must be positive")

        levels = self._levels_for(side)
        levels[price] = levels.get(price, 0.0) + quantity

    def best_bid(self) -> float | None:
        return max(self._bids) if self._bids else None

    def best_ask(self) -> float | None:
        return min(self._asks) if self._asks else None

    def mid_price(self) -> float | None:
        bid = self.best_bid()
        ask = self.best_ask()
        if bid is None or ask is None:
            return None
        return (bid + ask) / 2.0

    def spread(self) -> float | None:
        bid = self.best_bid()
        ask = self.best_ask()
        if bid is None or ask is None:
            return None
        return ask - bid

    def snapshot(self, depth: int = 5) -> dict[str, list[BookLevel]]:
        if depth <= 0:
            raise ValueError("depth must be positive")

        bids = sorted(self._bids.items(), reverse=True)[:depth]
        asks = sorted(self._asks.items())[:depth]
        return {
            "bids": [BookLevel(price, quantity) for price, quantity in bids],
            "asks": [BookLevel(price, quantity) for price, quantity in asks],
        }

    def _levels_for(self, side: str) -> dict[float, float]:
        normalized_side = side.lower()
        if normalized_side == "buy":
            return self._bids
        if normalized_side == "sell":
            return self._asks
        raise ValueError("side must be 'buy' or 'sell'")
