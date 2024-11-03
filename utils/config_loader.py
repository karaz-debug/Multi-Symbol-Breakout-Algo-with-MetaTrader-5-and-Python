# utils/config_loader.py

from dotenv import load_dotenv
import os
import logging

load_dotenv()

# Load MT5 credentials and server
MT5_LOGIN = os.getenv('MT5_LOGIN') or os.getenv('MT5_ACCOUNT')
if MT5_LOGIN is None:
    logging.error("MT5_LOGIN (or MT5_ACCOUNT) not set in .env file.")
    raise EnvironmentError("MT5_LOGIN (or MT5_ACCOUNT) not set in .env file.")

MT5_PASSWORD = os.getenv('MT5_PASSWORD')
if MT5_PASSWORD is None:
    logging.error("MT5_PASSWORD not set in .env file.")
    raise EnvironmentError("MT5_PASSWORD not set in .env file.")

MT5_SERVER = os.getenv('MT5_SERVER')
if MT5_SERVER is None:
    logging.error("MT5_SERVER not set in .env file.")
    raise EnvironmentError("MT5_SERVER not set in .env file.")

# Load symbol filters
SYMBOL_FILTER = os.getenv('SYMBOL_FILTER')
if SYMBOL_FILTER is None:
    logging.error("SYMBOL_FILTER not set in .env file.")
    raise EnvironmentError("SYMBOL_FILTER not set in .env file.")
SYMBOL_FILTER = [filter_currency.strip().upper() for filter_currency in SYMBOL_FILTER.split(',')]

# Load exclusion symbols if any
EXCLUDE_SYMBOLS = os.getenv('EXCLUDE_SYMBOLS')
if EXCLUDE_SYMBOLS:
    EXCLUDE_SYMBOLS = [symbol.strip().upper() for symbol in EXCLUDE_SYMBOLS.split(',')]
else:
    EXCLUDE_SYMBOLS = []

# Load excluded strategies if any
EXCLUDED_STRATEGIES = os.getenv('EXCLUDED_STRATEGIES')
if EXCLUDED_STRATEGIES:
    EXCLUDED_STRATEGIES = [symbol.strip().upper() for symbol in EXCLUDED_STRATEGIES.split(',')]
else:
    EXCLUDED_STRATEGIES = []

INITIAL_CAPITAL = float(os.getenv('INITIAL_CAPITAL', 49999))
RISK_PER_TRADE = float(os.getenv('RISK_PER_TRADE', 1.0))
MAGIC_NUMBER = int(os.getenv('MAGIC_NUMBER', 234000))
