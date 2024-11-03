# risk_management/risk_manager.py

import logging
import MetaTrader5 as mt5

class RiskManager:
    def __init__(self, mt5_connector, symbol, risk_per_trade=1.0):
        self.mt5 = mt5_connector
        self.symbol = symbol
        self.risk_per_trade = risk_per_trade  # Percentage of account to risk

    def calculate_lot_size(self, sl_pips, pip_value):
        """
        Calculate lot size based on risk per trade and stop-loss in pips.
        """
        account_info = mt5.account_info()
        if account_info is None:
            logging.error("Failed to retrieve account information.")
            return 0.01  # Default lot size

        balance = account_info.balance
        risk_amount = balance * (self.risk_per_trade / 100)
        if sl_pips == 0:
            logging.warning("Stop-Loss pips is zero. Setting lot size to minimum 0.01.")
            return 0.01

        lot_size = risk_amount / (sl_pips * pip_value * 10)  # Adjust multiplier as per broker
        return round(lot_size, 2)
