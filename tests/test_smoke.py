import sys
import unittest
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from market_making_simulation import LimitOrderBook, MarketMaker


class MarketMakingSmokeTest(unittest.TestCase):
    def test_market_maker_quotes_around_book_mid_price(self) -> None:
        book = LimitOrderBook()
        book.add_limit_order("buy", price=99.0, quantity=10.0)
        book.add_limit_order("sell", price=101.0, quantity=12.0)

        maker = MarketMaker(spread=0.5, quote_size=2.0)
        quote = maker.quote_from_book(book)

        self.assertIsNotNone(quote)
        assert quote is not None
        self.assertEqual(book.mid_price(), 100.0)
        self.assertEqual(book.spread(), 2.0)
        self.assertEqual(quote.bid_price, 99.75)
        self.assertEqual(quote.ask_price, 100.25)
        self.assertEqual(quote.bid_size, 2.0)
        self.assertEqual(quote.ask_size, 2.0)


if __name__ == "__main__":
    unittest.main()
