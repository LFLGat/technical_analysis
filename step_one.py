import yfinance as yf
import pandas as pd
import mplfinance as mpf
import numpy as np
import matplotlib.pyplot as plt
from scipy.signal import find_peaks

def find_significant_levels(data, prominence=2, cluster_distance_factor=0.5):
    """
    Identify significant levels based on prominent highs and lows and combine clusters into single levels.
    """
    highs = data['High']
    lows = data['Low']
    price_range = highs.max() - lows.min()
    adjusted_cluster_distance = price_range * cluster_distance_factor / 100

    # Find prominent peaks and troughs
    peak_indices, _ = find_peaks(highs, prominence=prominence)
    trough_indices, _ = find_peaks(-lows, prominence=prominence)

    peak_levels = highs.iloc[peak_indices].values
    trough_levels = lows.iloc[trough_indices].values

    # Combine levels
    all_levels = np.sort(np.concatenate([peak_levels, trough_levels]))

    # Cluster and combine levels
    clusters = []
    current_cluster = [all_levels[0]]

    for level in all_levels[1:]:
        if level - current_cluster[-1] <= adjusted_cluster_distance:
            current_cluster.append(level)
        else:
            clusters.append(current_cluster)
            current_cluster = [level]
    clusters.append(current_cluster)

    # Use the average of each cluster as the significant level
    significant_levels = [np.mean(cluster) for cluster in clusters]
    return significant_levels

def add_horizontal_lines(ax, levels):
    """
    Add horizontal lines at the specified levels on the plot.
    """
    for level in levels:
        ax.axhline(y=level, color='yellow', linestyle='--', linewidth=1)

def analyze_and_filter_levels(data_1m, levels_1m, data_5m, data_15m, data_1h):
    """
    Analyze the 1-minute places of interest on the 5-minute, 15-minute, and 1-hour charts and filter out those that do not align.
    """
    valid_levels = []
    for level in levels_1m:
        if ((abs(data_5m['High'] - level) < 0.5).any() or (abs(data_5m['Low'] - level) < 0.5).any()) and \
           ((abs(data_15m['High'] - level) < 0.5).any() or (abs(data_15m['Low'] - level) < 0.5).any()) and \
           ((abs(data_1h['High'] - level) < 0.5).any() or (abs(data_1h['Low'] - level) < 0.5).any()):
            valid_levels.append(level)
    return valid_levels

def main():
    # Define the stock symbol and date range
    symbol = "NVDA"
    start_date = "2024-06-24"
    end_date = "2024-06-29"
    interval_1m = "1m"
    interval_5m = "5m"
    interval_15m = "15m"
    interval_1h = "1h"

    # Fetch 1-minute data
    try:
        data_1m = yf.download(symbol, start=start_date, end=end_date, interval=interval_1m)
        if data_1m.empty:
            raise ValueError(f"No data found for {symbol} in the given date range with {interval_1m} interval.")
    except Exception as e:
        print(f"Error fetching 1-minute data: {e}")
        return

    # Find significant levels on the 1-minute data
    significant_levels_1m = find_significant_levels(data_1m)

    # Fetch 5-minute data
    try:
        data_5m = yf.download(symbol, start=start_date, end=end_date, interval=interval_5m)
        if data_5m.empty:
            raise ValueError(f"No data found for {symbol} in the given date range with {interval_5m} interval.")
    except Exception as e:
        print(f"Error fetching 5-minute data: {e}")
        return

    # Fetch 15-minute data
    try:
        data_15m = yf.download(symbol, start=start_date, end=end_date, interval=interval_15m)
        if data_15m.empty:
            raise ValueError(f"No data found for {symbol} in the given date range with {interval_15m} interval.")
    except Exception as e:
        print(f"Error fetching 15-minute data: {e}")
        return

    # Fetch 1-hour data
    try:
        data_1h = yf.download(symbol, start=start_date, end=end_date, interval=interval_1h)
        if data_1h.empty:
            raise ValueError(f"No data found for {symbol} in the given date range with {interval_1h} interval.")
    except Exception as e:
        print(f"Error fetching 1-hour data: {e}")
        return

    # Analyze and filter levels
    valid_levels = analyze_and_filter_levels(data_1m, significant_levels_1m, data_5m, data_15m, data_1h)

    # Print valid significant levels
    print("Valid Significant Levels (Places of Interest):")
    for level in valid_levels:
        print(f"{level:.2f}")

    # Plot the candlestick charts with valid significant levels
    try:
        fig, axes = plt.subplots(4, 1, figsize=(12, 24))

        # 1-minute chart
        mpf.plot(data_1m, type='candle', style='charles', axtitle=f'{symbol} - 1 Minute Interval', ylabel='Price', ax=axes[0], volume=False, warn_too_much_data=len(data_1m)+1)
        add_horizontal_lines(axes[0], significant_levels_1m)

        # 5-minute chart
        mpf.plot(data_5m, type='candle', style='charles', axtitle=f'{symbol} - 5 Minute Interval', ylabel='Price', ax=axes[1], volume=False, warn_too_much_data=len(data_5m)+1)
        add_horizontal_lines(axes[1], valid_levels)

        # 15-minute chart
        mpf.plot(data_15m, type='candle', style='charles', axtitle=f'{symbol} - 15 Minute Interval', ylabel='Price', ax=axes[2], volume=False, warn_too_much_data=len(data_15m)+1)
        add_horizontal_lines(axes[2], valid_levels)

        # 1-hour chart
        mpf.plot(data_1h, type='candle', style='charles', axtitle=f'{symbol} - 1 Hour Interval', ylabel='Price', ax=axes[3], volume=False, warn_too_much_data=len(data_1h)+1)
        add_horizontal_lines(axes[3], valid_levels)

        plt.tight_layout()
        plt.show(block=True)  # Ensure that the plot is shown
    except Exception as e:
        print(f"Error plotting data: {e}")

if __name__ == "__main__":
    main()
