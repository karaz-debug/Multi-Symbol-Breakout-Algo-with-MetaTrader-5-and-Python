# utils/symbol_manager.py

import logging
import MetaTrader5 as mt5
from utils.config_loader import SYMBOL_FILTER, EXCLUDE_SYMBOLS, EXCLUDED_STRATEGIES

def fetch_filtered_symbols():
    """
    Fetch and filter symbols based on SYMBOL_FILTER, EXCLUDE_SYMBOLS, and EXCLUDED_STRATEGIES.
    :return: List of filtered symbols.
    """
    all_symbols = mt5.symbols_get()
    if not all_symbols:
        logging.error("No symbols retrieved from MT5.")
        raise ValueError("No symbols retrieved from MT5.")

    filtered_symbols = []
    for symbol in all_symbols:
        symbol_name = symbol.name.upper()
        # Check if symbol contains any of the filter currencies
        if any(filter_currency in symbol_name for filter_currency in SYMBOL_FILTER):
            # Exclude symbols if in exclusion lists
            if symbol_name not in EXCLUDE_SYMBOLS and symbol_name not in EXCLUDED_STRATEGIES:
                filtered_symbols.append(symbol_name)
            else:
                logging.debug(f"Excluded symbol: {symbol_name}")
        else:
            logging.debug(f"Symbol does not match filters and is excluded: {symbol_name}")

    if not filtered_symbols:
        logging.error("No symbols matched the specified filters.")
        raise ValueError("No symbols matched the specified filters.")

    logging.info(f"Filtered symbols: {filtered_symbols}")
    return filtered_symbols
