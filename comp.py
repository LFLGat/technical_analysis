import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt

def fetch_data(ticker, start_date, end_date, interval):
    return yf.download(ticker, start=start_date, end=end_date, interval=interval)

def plot_trends(stock_data, sector_data, index_data, stock_ticker, sector_ticker, index_ticker):
    plt.figure(figsize=(14, 10))

    plt.subplot(3, 1, 1)
    plt.plot(index_data['Close'], label=f'{index_ticker} Close')
    plt.title(f'{index_ticker} Trend')
    plt.legend()

    plt.subplot(3, 1, 2)
    plt.plot(sector_data['Close'], label=f'{sector_ticker} Close')
    plt.title(f'{sector_ticker} Trend')
    plt.legend()

    plt.subplot(3, 1, 3)
    plt.plot(stock_data['Close'], label=f'{stock_ticker} Close')
    plt.title(f'{stock_ticker} Trend')
    plt.legend()

    plt.tight_layout()
    plt.show()

def main():
    # Define the tickers and date range
    stock_ticker = "NVDA"
    sector_ticker = "XLK"  # Technology Select Sector SPDR Fund
    index_ticker = "^GSPC"  # S&P 500 Index
    start_date = "2024-06-24"
    end_date = "2024-06-29"
    interval = "1h"  # Use 1-hour interval for this analysis

    # Fetch data
    stock_data = fetch_data(stock_ticker, start_date, end_date, interval)
    sector_data = fetch_data(sector_ticker, start_date, end_date, interval)
    index_data = fetch_data(index_ticker, start_date, end_date, interval)

    # Plot the trends
    plot_trends(stock_data, sector_data, index_data, stock_ticker, sector_ticker, index_ticker)

if __name__ == "__main__":
    main()
