from __future__ import annotations

from dataclasses import dataclass

from .order_book import LimitOrderBook


@dataclass(frozen=True)
class Quote:
    bid_price: float
    ask_price: float
    bid_size: float
    ask_size: float


@dataclass(frozen=True)
class MarketMaker:
    spread: float = 1.0
    quote_size: float = 1.0

    def __post_init__(self) -> None:
        if self.spread <= 0:
            raise ValueError("spread must be positive")
        if self.quote_size <= 0:
            raise ValueError("quote_size must be positive")

    def quote(self, reference_price: float) -> Quote:
        if reference_price <= 0:
            raise ValueError("reference_price must be positive")

        half_spread = self.spread / 2.0
        return Quote(
            bid_price=reference_price - half_spread,
            ask_price=reference_price + half_spread,
            bid_size=self.quote_size,
            ask_size=self.quote_size,
        )

    def quote_from_book(self, order_book: LimitOrderBook) -> Quote | None:
        mid_price = order_book.mid_price()
        if mid_price is None:
            return None
        return self.quote(mid_price)
