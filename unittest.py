import unittest
import pandas as pd
from strategies.breakout_mtf_strategy import BreakoutMTFStrategy
import MetaTrader5 as mt5

class TestBreakoutMTFStrategy(unittest.TestCase):
    def setUp(self):
        # Initialize MT5 connection for testing
        if not mt5.initialize():
            raise ConnectionError("MT5 initialization failed for testing.")
        self.strategy = BreakoutMTFStrategy(mt5_connector=mt5, symbol='EURUSD', risk_per_trade=1.0, magic_number=234000)
        self.strategy.fetch_initial_data()

    def tearDown(self):
        mt5.shutdown()

    def test_moving_averages(self):
        # Test if moving averages are calculated correctly
        self.assertIn('short_ma', self.strategy.higher_tf_data.columns)
        self.assertIn('long_ma', self.strategy.higher_tf_data.columns)
        self.assertFalse(self.strategy.higher_tf_data['short_ma'].isnull().all(), "Short MA should not be all NaN.")
        self.assertFalse(self.strategy.higher_tf_data['long_ma'].isnull().all(), "Long MA should not be all NaN.")

    def test_support_resistance(self):
        # Test if support and resistance are calculated as scalars
        support = self.strategy.calculate_support()
        resistance = self.strategy.calculate_resistance()
        self.assertIsInstance(support, float, "Support should be a float.")
        self.assertIsInstance(resistance, float, "Resistance should be a float.")

    def test_analyze_market_no_error(self):
        # Ensure that analyze_market runs without raising exceptions
        try:
            self.strategy.analyze_market()
        except Exception as e:
            self.fail(f"analyze_market raised an exception {e}")

if __name__ == '__main__':
    unittest.main()
