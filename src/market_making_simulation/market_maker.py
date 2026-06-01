from __future__ import annotations

from dataclasses import dataclass

from .order_book import LimitOrderBook


@dataclass(frozen=True)
class Quote:
    """Bid and ask prices posted by the market maker for one time step."""

    bid_price: float
    ask_price: float
    bid_size: float
    ask_size: float


@dataclass(frozen=True)
class MarketMaker:
    """Small legacy fixed-spread market maker used by the order book smoke test."""

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


@dataclass(frozen=True)
class ConstantSpreadMarketMaker:
    """Post a fixed half-spread around fair value with no inventory adjustment.

    A half-spread of 0.50 means the bid is fair_value - 0.50 and the ask is
    fair_value + 0.50. This is the simplest market-making benchmark.
    """

    half_spread: float = 0.5
    quote_size: float = 1.0

    @property
    def name(self) -> str:
        return "constant_spread"

    @property
    def inventory_penalty(self) -> float:
        return 0.0

    def __post_init__(self) -> None:
        if self.half_spread <= 0:
            raise ValueError("half_spread must be positive")
        if self.quote_size <= 0:
            raise ValueError("quote_size must be positive")

    def quote(self, fair_value: float, inventory: float = 0.0) -> Quote:
        if fair_value <= 0:
            raise ValueError("fair_value must be positive")

        return Quote(
            bid_price=max(0.01, fair_value - self.half_spread),
            ask_price=fair_value + self.half_spread,
            bid_size=self.quote_size,
            ask_size=self.quote_size,
        )


@dataclass(frozen=True)
class InventoryAwareMarketMaker:
    """Fixed-spread market maker with a simple inventory-aware reservation price.

    The reservation price is fair_value - inventory_penalty * inventory. Positive
    inventory lowers the reservation price, which lowers the ask and makes selling
    inventory more likely. Negative inventory raises the reservation price, which
    raises the bid and makes buying back inventory more likely. This mirrors the
    intuition of Avellaneda-Stoikov without solving the full control problem.
    """

    half_spread: float = 0.5
    quote_size: float = 1.0
    inventory_penalty: float = 0.02

    @property
    def name(self) -> str:
        return "inventory_aware"

    def __post_init__(self) -> None:
        if self.half_spread <= 0:
            raise ValueError("half_spread must be positive")
        if self.quote_size <= 0:
            raise ValueError("quote_size must be positive")
        if self.inventory_penalty < 0:
            raise ValueError("inventory_penalty must be non-negative")

    def quote(self, fair_value: float, inventory: float = 0.0) -> Quote:
        if fair_value <= 0:
            raise ValueError("fair_value must be positive")

        reservation_price = fair_value - self.inventory_penalty * inventory
        bid_price = max(0.01, reservation_price - self.half_spread)
        ask_price = max(bid_price + 0.01, reservation_price + self.half_spread)
        return Quote(
            bid_price=bid_price,
            ask_price=ask_price,
            bid_size=self.quote_size,
            ask_size=self.quote_size,
        )
