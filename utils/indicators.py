# utils/indicators.py

import pandas as pd

def calculate_moving_average(series, window):
    """
    Calculate the moving average for a given pandas Series and window size.
    :param series: pandas Series of prices.
    :param window: Window size for moving average.
    :return: pandas Series of moving averages.
    """
    return series.rolling(window=window).mean()
