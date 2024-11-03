# live_trading/mt5_connector.py

import MetaTrader5 as mt5
import logging
from utils.config_loader import MT5_LOGIN, MT5_PASSWORD, MT5_SERVER
from utils.symbol_manager import fetch_filtered_symbols

def initialize_mt5():
    """
    Initialize connection to MetaTrader 5.
    :return: Tuple containing MT5 connection and list of filtered symbols.
    """
    if not mt5.initialize():
        logging.error("Failed to initialize MT5")
        raise ConnectionError("MT5 initialization failed")
    
    authorized = mt5.login(
        login=int(MT5_LOGIN),
        password=MT5_PASSWORD,
        server=MT5_SERVER
    )
    
    if not authorized:
        logging.error(f"MT5 login failed: {mt5.last_error()}")
        mt5.shutdown()
        raise ConnectionError("MT5 login failed")
    
    logging.info("MT5 initialized and logged in successfully")

    # Fetch filtered symbols
    SYMBOLS = fetch_filtered_symbols()
    logging.info(f"Filtered symbols: {SYMBOLS}")

    # Enable each filtered symbol
    enabled_symbols = []
    for symbol in SYMBOLS:
        if not mt5.symbol_select(symbol, True):
            logging.error(f"Failed to enable symbol: {symbol}")
        else:
            enabled_symbols.append(symbol)
            logging.info(f"Symbol enabled: {symbol}")
    
    if not enabled_symbols:
        logging.error("No symbols were successfully enabled.")
        raise ValueError("No symbols were successfully enabled.")
    
    logging.info(f"Final enabled symbols: {enabled_symbols}")
    return mt5, enabled_symbols

def shutdown_mt5():
    """
    Shutdown the MT5 connection.
    """
    mt5.shutdown()
    logging.info("MT5 connection shut down.")
