# live_trading/live_trading.py

import asyncio
import logging
from live_trading.mt5_connector import initialize_mt5, shutdown_mt5
from strategies.breakout_mtf_strategy import BreakoutMTFStrategy
from utils.logger import setup_logger
from utils.config_loader import INITIAL_CAPITAL, RISK_PER_TRADE, MAGIC_NUMBER, EXCLUDED_STRATEGIES

async def monitor_symbol(strategy):
    """
    Coroutine to monitor and analyze market data for a specific symbol.
    """
    while True:
        try:
            strategy.analyze_market()
        except Exception as e:
            logging.error(f"Error in monitoring {strategy.symbol}: {e}")
        await asyncio.sleep(300)  # Sleep for 5 minutes if primary_tf is 'M5'

async def main():
    """
    Main coroutine to initialize strategies and manage live trading.
    """
    setup_logger()
    try:
        # Initialize MT5 and fetch the list of enabled symbols
        mt5_connection, SYMBOLS = initialize_mt5()
        logging.info(f"Final SYMBOLS list: {SYMBOLS}")
        strategies = {}

        # Initialize strategy instances for each symbol
        for symbol in SYMBOLS:
            if symbol in EXCLUDED_STRATEGIES:
                logging.info(f"Skipping excluded symbol: {symbol}")
                continue  # Skip initializing strategy for excluded symbols

            try:
                strategy = BreakoutMTFStrategy(
                    mt5_connector=mt5_connection,
                    symbol=symbol,
                    risk_per_trade=RISK_PER_TRADE,
                    magic_number=MAGIC_NUMBER  # Pass the magic number here
                )
                strategy.fetch_initial_data()
                strategies[symbol] = strategy
                logging.info(f"Strategy initialized for {symbol}")
            except Exception as e:
                logging.error(f"Failed to initialize strategy for {symbol}: {e}", exc_info=True)
                # Optionally, you can remove the symbol from the SYMBOLS list if initialization fails
                # SYMBOLS.remove(symbol)

        # Check if any strategies were initialized
        if not strategies:
            logging.warning("No strategies were initialized. Exiting the trading system.")
            return

        # Create and gather tasks for each symbol
        tasks = [monitor_symbol(strategy) for strategy in strategies.values()]
        await asyncio.gather(*tasks)
    except Exception as e:
        logging.critical(f"Unexpected error in main: {e}", exc_info=True)
    finally:
        shutdown_mt5()

if __name__ == "__main__":
    asyncio.run(main())
