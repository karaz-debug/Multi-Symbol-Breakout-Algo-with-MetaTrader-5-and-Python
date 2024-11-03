# strategies/breakout_mtf_strategy.py

from .base_strategy import BaseStrategy
import pandas as pd
import logging
from utils.indicators import calculate_moving_average
from risk_management.risk_manager import RiskManager
import MetaTrader5 as mt5
import requests

def send_telegram_message(bot_token, chat_id, message):
    """
    Send a message to a Telegram chat using a bot.

    :param bot_token: Token of the Telegram bot.
    :param chat_id: Chat ID where the message will be sent.
    :param message: The message content.
    """
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {
        'chat_id': chat_id,
        'text': message,
        'parse_mode': 'HTML'  # Optional: Allows HTML formatting
    }
    try:
        response = requests.post(url, data=payload)
        if response.status_code != 200:
            logging.error(f"Failed to send Telegram message: {response.text}")
    except Exception as e:
        logging.error(f"Exception occurred while sending Telegram message: {e}")

class BreakoutMTFStrategy(BaseStrategy):
    """
    Multi-Timeframe Breakout Strategy adapted for Live Trading on MT5.
    Buys when the price breaks above the higher timeframe resistance level and the higher timeframe trend is bullish.
    Sells when the price breaks below the higher timeframe support level and the higher timeframe trend is bearish.
    Executes trades on the primary (current) timeframe with defined Stop-Loss (SL) and Take-Profit (TP).
    """

    def __init__(self, mt5_connector, symbol, risk_per_trade=1.0, magic_number=234000):
        super().__init__()
        self.mt5 = mt5_connector
        self.symbol = symbol
        self.risk_per_trade = risk_per_trade
        self.magic_number = magic_number  # Store the magic number
        self.data = pd.DataFrame()
        self.higher_tf_data = pd.DataFrame()
        self.current_higher_index = 0
        self.prev_higher_short_ma = None
        self.prev_higher_long_ma = None
        self.risk_manager = RiskManager(mt5_connector=self.mt5, symbol=self.symbol, risk_per_trade=self.risk_per_trade)
        self.strategy_params = {
            'tp_percent': 14.0,
            'sl_percent': 11.0,
            'higher_tf_short_ma': 20,
            'higher_tf_long_ma': 50,
            'primary_tf': mt5.TIMEFRAME_M5,  # 5-minute timeframe
            'higher_tf': mt5.TIMEFRAME_H1,   # 1-hour timeframe
            'support_resistance_window': 10,  # Window size for support/resistance
        }
        # Telegram configurations
        self.telegram_bot_token = '8142388383:AAHKT5wZ4UQylWCHG5l5vGruKGoqOGfBcjA'  # Replace with your new token
        self.telegram_chat_id = '1327792287'  # Replace with your actual Chat ID

    def fetch_initial_data(self):
        """
        Fetch historical data from MT5 for both primary and higher timeframes to initialize indicators.
        Calculate support and resistance based on the backtest logic.
        """
        primary_tf = self.strategy_params['primary_tf']  # 5-minute timeframe
        higher_tf = self.strategy_params['higher_tf']    # 1-hour timeframe
        window = self.strategy_params['support_resistance_window']

        # Fetch historical data for primary timeframe
        rates_primary = mt5.copy_rates_from_pos(self.symbol, primary_tf, 0, 500)
        if rates_primary is None or len(rates_primary) == 0:
            logging.error(f"No primary timeframe data retrieved for {self.symbol}")
            raise ValueError(f"No primary timeframe data retrieved for {self.symbol}")
        
        self.data = pd.DataFrame(rates_primary)
        self.data['time'] = pd.to_datetime(self.data['time'], unit='s')
        self.data.set_index('time', inplace=True)
        # Remove duplicate indices
        self.data = self.data[~self.data.index.duplicated(keep='last')]
        # Sort the index
        self.data = self.data.sort_index()
        # Assert uniqueness
        assert self.data.index.is_unique, "Primary timeframe data index is not unique."
        logging.debug(f"Primary DataFrame for {self.symbol} has {len(self.data)} unique entries.")

        # Fetch historical data for higher timeframe
        rates_higher = mt5.copy_rates_from_pos(self.symbol, higher_tf, 0, 500)
        if rates_higher is None or len(rates_higher) == 0:
            logging.error(f"No higher timeframe data retrieved for {self.symbol}")
            raise ValueError(f"No higher timeframe data retrieved for {self.symbol}")
        
        self.higher_tf_data = pd.DataFrame(rates_higher)
        self.higher_tf_data['time'] = pd.to_datetime(self.higher_tf_data['time'], unit='s')
        self.higher_tf_data.set_index('time', inplace=True)
        # Remove duplicate indices
        self.higher_tf_data = self.higher_tf_data[~self.higher_tf_data.index.duplicated(keep='last')]
        # Sort the index
        self.higher_tf_data = self.higher_tf_data.sort_index()
        # Assert uniqueness
        assert self.higher_tf_data.index.is_unique, "Higher timeframe data index is not unique."
        logging.debug(f"Higher TF DataFrame for {self.symbol} has {len(self.higher_tf_data)} unique entries.")

        # Calculate moving averages
        self.higher_tf_data['short_ma'] = calculate_moving_average(
            self.higher_tf_data['close'], self.strategy_params['higher_tf_short_ma']
        )
        self.higher_tf_data['long_ma'] = calculate_moving_average(
            self.higher_tf_data['close'], self.strategy_params['higher_tf_long_ma']
        )

        # Calculate support and resistance based on the specified window
        self.higher_tf_data['support'] = self.higher_tf_data['low'].rolling(window=window).min()
        self.higher_tf_data['resistance'] = self.higher_tf_data['high'].rolling(window=window).max()

        # Align support and resistance with primary timeframe using forward fill
        self.higher_support = self.higher_tf_data['support'].reindex(self.data.index, method='ffill')
        self.higher_resistance = self.higher_tf_data['resistance'].reindex(self.data.index, method='ffill')

        # Initialize index pointer for higher timeframe data
        self.current_higher_index = 0

        # Initialize previous higher timeframe moving averages for trend determination
        self.prev_higher_short_ma = None
        self.prev_higher_long_ma = None

        logging.info(f"Initial data fetched and moving averages, support, resistance calculated for {self.symbol}")

    def update_data(self):
        """
        Fetch the latest bar from MT5 and update dataframes.
        Calculate updated moving averages, support, and resistance.
        """
        primary_tf = self.strategy_params['primary_tf']  # 5-minute timeframe
        higher_tf = self.strategy_params['higher_tf']    # 1-hour timeframe
        window = self.strategy_params['support_resistance_window']

        # Fetch the latest bar for primary timeframe
        latest_primary = mt5.copy_rates_from_pos(self.symbol, primary_tf, 0, 1)
        if latest_primary is not None and len(latest_primary) > 0:
            latest_primary_df = pd.DataFrame(latest_primary)
            latest_primary_df['time'] = pd.to_datetime(latest_primary_df['time'], unit='s')
            latest_primary_df.set_index('time', inplace=True)
            # Check if the latest timestamp already exists
            if latest_primary_df.index[-1] not in self.data.index:
                self.data = pd.concat([self.data, latest_primary_df])
                # Remove duplicate indices
                self.data = self.data[~self.data.index.duplicated(keep='last')]
                # Sort the index
                self.data = self.data.sort_index()
                # Assert uniqueness
                assert self.data.index.is_unique, "Primary timeframe data index is not unique after update."
                logging.debug(f"New primary data appended for {self.symbol}. Total entries: {len(self.data)}")
            else:
                logging.debug(f"No new primary data for {self.symbol}")

        # Fetch the latest bar for higher timeframe
        latest_higher = mt5.copy_rates_from_pos(self.symbol, higher_tf, 0, 1)
        if latest_higher is not None and len(latest_higher) > 0:
            latest_higher_df = pd.DataFrame(latest_higher)
            latest_higher_df['time'] = pd.to_datetime(latest_higher_df['time'], unit='s')
            latest_higher_df.set_index('time', inplace=True)
            # Check if the latest timestamp already exists
            if latest_higher_df.index[-1] not in self.higher_tf_data.index:
                self.higher_tf_data = pd.concat([self.higher_tf_data, latest_higher_df])
                # Remove duplicate indices
                self.higher_tf_data = self.higher_tf_data[~self.higher_tf_data.index.duplicated(keep='last')]
                # Sort the index
                self.higher_tf_data = self.higher_tf_data.sort_index()
                # Assert uniqueness
                assert self.higher_tf_data.index.is_unique, "Higher timeframe data index is not unique after update."

                # Recalculate moving averages
                self.higher_tf_data['short_ma'] = calculate_moving_average(
                    self.higher_tf_data['close'], self.strategy_params['higher_tf_short_ma']
                )
                self.higher_tf_data['long_ma'] = calculate_moving_average(
                    self.higher_tf_data['close'], self.strategy_params['higher_tf_long_ma']
                )

                # Recalculate support and resistance
                self.higher_tf_data['support'] = self.higher_tf_data['low'].rolling(window=window).min()
                self.higher_tf_data['resistance'] = self.higher_tf_data['high'].rolling(window=window).max()

                # Reindex support and resistance
                self.higher_support = self.higher_tf_data['support'].reindex(self.data.index, method='ffill')
                self.higher_resistance = self.higher_tf_data['resistance'].reindex(self.data.index, method='ffill')

                logging.debug(f"New higher timeframe data appended and support/resistance recalculated for {self.symbol}. Total entries: {len(self.higher_tf_data)}")
            else:
                logging.debug(f"No new higher timeframe data for {self.symbol}")

    def analyze_market(self):
        """
        Analyze the market and generate trading signals based on the strategy.
        """
        try:
            self.update_data()

            # Get the latest timestamp from primary timeframe
            current_time = self.data.index[-1]
            logging.debug(f"Current Time: {current_time}")
        
            # Determine if a new higher timeframe bar has formed
            if current_time in self.higher_tf_data.index:
                self.current_higher_index = self.higher_tf_data.index.get_loc(current_time)
                logging.debug(f"New higher timeframe bar detected at index {self.current_higher_index}")
            else:
                logging.debug("No new higher timeframe bar detected.")
                return  # No new higher timeframe bar, no action needed

            # Get current higher timeframe moving averages
            higher_short_ma = self.higher_tf_data['short_ma'].iloc[self.current_higher_index]
            higher_long_ma = self.higher_tf_data['long_ma'].iloc[self.current_higher_index]
            logging.debug(f"Higher Short MA: {higher_short_ma}, Higher Long MA: {higher_long_ma}")

            # Check if moving averages are valid
            if pd.isna(higher_short_ma) or pd.isna(higher_long_ma):
                logging.debug("HTF moving averages are NaN, skipping signal generation.")
                return  # Not enough data to compute moving averages

            # Determine higher timeframe trend
            if self.prev_higher_short_ma is not None and self.prev_higher_long_ma is not None:
                trend_bullish = (
                    self.prev_higher_short_ma < self.prev_higher_long_ma and
                    higher_short_ma > higher_long_ma
                )
                trend_bearish = (
                    self.prev_higher_short_ma > self.prev_higher_long_ma and
                    higher_short_ma < higher_long_ma
                )
                logging.debug(f"Higher Trend Bullish: {trend_bullish}, Higher Trend Bearish: {trend_bearish}")
                if trend_bullish:
                    logging.info(f"Higher timeframe trend is bullish for {self.symbol}.")
                elif trend_bearish:
                    logging.info(f"Higher timeframe trend is bearish for {self.symbol}.")
                else:
                    logging.info(f"Higher timeframe trend is neutral for {self.symbol}.")
            else:
                trend_bullish = False
                trend_bearish = False
                logging.debug("No previous HTF moving averages to determine trend.")

            # Update previous higher timeframe moving averages
            self.prev_higher_short_ma = higher_short_ma
            self.prev_higher_long_ma = higher_long_ma

            # Fetch support and resistance levels from higher_tf_data
            support = self.higher_support.iloc[self.current_higher_index]
            resistance = self.higher_resistance.iloc[self.current_higher_index]
            logging.debug(f"Support for {self.symbol}: {support}")
            logging.debug(f"Resistance for {self.symbol}: {resistance}")

            # Get current close price
            current_close = self.data['close'].iloc[-1]
            logging.debug(f"Current Close Price: {current_close}")

            # Check for breakout above resistance
            if current_close > resistance and trend_bullish:
                logging.info(f"Buy Signal Detected for {self.symbol} at {current_close}")
                message = f"<b>Buy Signal</b> for <b>{self.symbol}</b> at <b>{current_close}</b>\nSupport: {support}\nResistance: {resistance}"
                send_telegram_message(self.telegram_bot_token, self.telegram_chat_id, message)
                self.execute_order('BUY', current_close, resistance)

            # Check for breakout below support
            if current_close < support and trend_bearish:
                logging.info(f"Sell Signal Detected for {self.symbol} at {current_close}")
                message = f"<b>Sell Signal</b> for <b>{self.symbol}</b> at <b>{current_close}</b>\nSupport: {support}\nResistance: {resistance}"
                send_telegram_message(self.telegram_bot_token, self.telegram_chat_id, message)
                self.execute_order('SELL', current_close, support)

        except Exception as e:
            logging.error(f"Error in analyze_market: {e}", exc_info=True)

    def execute_order(self, order_type, entry_price, level):
        """
        Execute buy or sell orders based on the signal with risk management.
        """
        try:
            # Define Stop-Loss (SL) and Take-Profit (TP) based on percentage
            if order_type == 'BUY':
                sl = entry_price * (1 - self.strategy_params['sl_percent'] / 100)
                tp = entry_price * (1 + self.strategy_params['tp_percent'] / 100)
            elif order_type == 'SELL':
                sl = entry_price * (1 + self.strategy_params['sl_percent'] / 100)
                tp = entry_price * (1 - self.strategy_params['tp_percent'] / 100)
            else:
                logging.error(f"Invalid order type: {order_type}")
                return

            # Fetch symbol information to determine pip value
            symbol_info = mt5.symbol_info(self.symbol)
            if symbol_info is None:
                logging.error(f"Symbol {self.symbol} not found.")
                return
            digits = symbol_info.digits
            pip_value = 0.0001 if digits > 2 else 0.01

            # Calculate Stop-Loss in pips
            sl_pips = abs(entry_price - sl) / pip_value

            # Calculate lot size using risk management
            lot_size = self.risk_manager.calculate_lot_size(sl_pips, pip_value)

            # Ensure that lot size meets broker's minimum requirements
            lot_size = max(lot_size, 0.01)  # Example: minimum lot size 0.01

            # Create order request
            request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "symbol": self.symbol,
                "volume": lot_size,
                "type": mt5.ORDER_TYPE_BUY if order_type == 'BUY' else mt5.ORDER_TYPE_SELL,
                "price": entry_price,
                "sl": sl,
                "tp": tp,
                "deviation": 20,  # Adjust as needed
                "magic": self.magic_number,  # Use the configured magic number
                "comment": "Python MT5 EA",
                "type_time": mt5.ORDER_TIME_GTC,
                "type_filling": mt5.ORDER_FILLING_IOC,
            }

            # Send order
            result = mt5.order_send(request)

            # Check result
            if result.retcode == mt5.TRADE_RETCODE_DONE:
                logging.info(f"Executed {order_type} order for {self.symbol} at {entry_price} with SL={sl} and TP={tp}")
                order_message = (
                    f"<b>Order Executed</b>\n"
                    f"Symbol: {self.symbol}\n"
                    f"Type: {order_type}\n"
                    f"Entry Price: {entry_price}\n"
                    f"SL: {sl}\n"
                    f"TP: {tp}\n"
                    f"Volume: {lot_size}"
                )
                send_telegram_message(self.telegram_bot_token, self.telegram_chat_id, order_message)
            else:
                error_message = (
                    f"<b>Order Failed</b>\n"
                    f"Symbol: {self.symbol}\n"
                    f"Type: {order_type}\n"
                    f"Reason: {result.retcode} - {mt5.last_error()}"
                )
                logging.error(f"Order failed for {self.symbol}: {result.retcode} - {mt5.last_error()}")
                send_telegram_message(self.telegram_bot_token, self.telegram_chat_id, error_message)

        except Exception as e:
            logging.error(f"Error in execute_order: {e}", exc_info=True)
