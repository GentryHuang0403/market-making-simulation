import sys
import unittest
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from market_making_simulation import MarketMaker, run_simulation


class SimulationSmokeTest(unittest.TestCase):
    def test_simulation_records_price_inventory_cash_and_pnl(self) -> None:
        records = run_simulation(
            steps=3,
            initial_mid_price=100.0,
            price_tick=1.0,
            maker=MarketMaker(spread=0.5, quote_size=2.0),
            seed=1,
        )

        self.assertEqual(len(records), 3)
        self.assertEqual([record.step for record in records], [1, 2, 3])
        self.assertEqual([record.mid_price for record in records], [99.0, 98.0, 99.0])
        self.assertEqual([record.inventory for record in records], [2.0, 4.0, 2.0])
        self.assertEqual(records[0].cash, -197.5)
        self.assertEqual(records[2].cash, -194.5)
        self.assertEqual(records[0].bid_price, 98.75)
        self.assertEqual(records[2].ask_price, 99.25)
        self.assertAlmostEqual(records[0].pnl, 0.5)
        self.assertAlmostEqual(records[1].pnl, -1.0)
        self.assertAlmostEqual(records[2].pnl, 3.5)


if __name__ == "__main__":
    unittest.main()
