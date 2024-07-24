from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse, StreamingResponse, JSONResponse
from fastapi.templating import Jinja2Templates
import yfinance as yf
import pandas as pd
import numpy as np
from scipy.signal import find_peaks
import matplotlib.pyplot as plt
import mplfinance as mpf
import io
from mangum import Mangum

app = FastAPI()
templates = Jinja2Templates(directory="templates")

def find_significant_levels(data, prominence=2, cluster_distance_factor=0.5):
    highs = data['High']
    lows = data['Low']
    price_range = highs.max() - lows.min()
    adjusted_cluster_distance = price_range * cluster_distance_factor / 100

    peak_indices, _ = find_peaks(highs, prominence=prominence)
    trough_indices, _ = find_peaks(-lows, prominence=prominence)

    peak_levels = highs.iloc[peak_indices].values
    trough_levels = lows.iloc[trough_indices].values

    all_levels = np.sort(np.concatenate([peak_levels, trough_levels]))

    clusters = []
    current_cluster = [all_levels[0]]

    for level in all_levels[1:]:
        if level - current_cluster[-1] <= adjusted_cluster_distance:
            current_cluster.append(level)
        else:
            clusters.append(current_cluster)
            current_cluster = [level]
    clusters.append(current_cluster)

    significant_levels = [np.mean(cluster) for cluster in clusters]
    return significant_levels

def add_horizontal_lines(ax, levels):
    for level in levels:
        ax.axhline(y=level, color='yellow', linestyle='--', linewidth=1)
        ax.text(0.01, level, f'{level:.2f}', va='center', ha='left', color='red', transform=ax.get_yaxis_transform())

def analyze_and_filter_levels(data_1m, levels_1m, data_5m, data_15m, data_1h):
    valid_levels = []
    for level in levels_1m:
        if ((abs(data_5m['High'] - level) < 0.5).any() or (abs(data_5m['Low'] - level) < 0.5).any()) and \
           ((abs(data_15m['High'] - level) < 0.5).any() or (abs(data_15m['Low'] - level) < 0.5).any()) and \
           ((abs(data_1h['High'] - level) < 0.5).any() or (abs(data_1h['Low'] - level) < 0.5).any()):
            valid_levels.append(level)
    return valid_levels

def fetch_data(ticker, start_date, end_date, interval):
    return yf.download(ticker, start=start_date, end=end_date, interval=interval)

def determine_trend(data):
    short_ma = data['Close'].rolling(window=50).mean()
    long_ma = data['Close'].rolling(window=200).mean()
    if short_ma.iloc[-1] > long_ma.iloc[-1]:
        return "Bullish"
    else:
        return "Bearish"

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
    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    plt.close()
    return buf

@app.get("/", response_class=HTMLResponse)
async def read_form(request: Request):
    return templates.TemplateResponse("form.html", {"request": request})

@app.post("/plot/")
async def plot_significant_levels(
    request: Request,
    stock_ticker: str = Form(...),
    sector_ticker: str = Form(...),
    index_ticker: str = Form(...),
    start_date: str = Form(...),
    end_date: str = Form(...)
):
    data_1m = fetch_data(stock_ticker, start_date, end_date, "1m")
    data_5m = fetch_data(stock_ticker, start_date, end_date, "5m")
    data_15m = fetch_data(stock_ticker, start_date, end_date, "15m")
    data_1h = fetch_data(stock_ticker, start_date, end_date, "1h")

    if data_1m.empty or data_5m.empty or data_15m.empty or data_1h.empty:
        return JSONResponse(status_code=404, content={"message": "No data found for the given parameters."})

    significant_levels_1m = find_significant_levels(data_1m)
    valid_levels = analyze_and_filter_levels(data_1m, significant_levels_1m, data_5m, data_15m, data_1h)

    fig, axes = plt.subplots(4, 1, figsize=(12, 24))

    trend_1m = determine_trend(data_1m)
    trend_5m = determine_trend(data_5m)
    trend_15m = determine_trend(data_15m)
    trend_1h = determine_trend(data_1h)

    mpf.plot(data_1m, type='candle', style='charles', axtitle=f'{stock_ticker} - 1 Minute Interval ({trend_1m})', ylabel='Price', ax=axes[0], volume=False)
    add_horizontal_lines(axes[0], significant_levels_1m)

    mpf.plot(data_5m, type='candle', style='charles', axtitle=f'{stock_ticker} - 5 Minute Interval ({trend_5m})', ylabel='Price', ax=axes[1], volume=False)
    add_horizontal_lines(axes[1], valid_levels)

    mpf.plot(data_15m, type='candle', style='charles', axtitle=f'{stock_ticker} - 15 Minute Interval ({trend_15m})', ylabel='Price', ax=axes[2], volume=False)
    add_horizontal_lines(axes[2], valid_levels)

    mpf.plot(data_1h, type='candle', style='charles', axtitle=f'{stock_ticker} - 1 Hour Interval ({trend_1h})', ylabel='Price', ax=axes[3], volume=False)
    add_horizontal_lines(axes[3], valid_levels)

    plt.tight_layout()
    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    plt.close()
    return StreamingResponse(buf, media_type="image/png")

@app.post("/trends/")
async def plot_trends_endpoint(
    request: Request,
    stock_ticker: str = Form(...),
    sector_ticker: str = Form(...),
    index_ticker: str = Form(...),
    start_date: str = Form(...),
    end_date: str = Form(...)
):
    stock_data = fetch_data(stock_ticker, start_date, end_date, "1h")
    sector_data = fetch_data(sector_ticker, start_date, end_date, "1h")
    index_data = fetch_data(index_ticker, start_date, end_date, "1h")

    if stock_data.empty or sector_data.empty or index_data.empty:
        return JSONResponse(status_code=404, content={"message": "No data found for the given parameters."})

    buf = plot_trends(stock_data, sector_data, index_data, stock_ticker, sector_ticker, index_ticker)
    return StreamingResponse(buf, media_type="image/png")

handler = Mangum(app)
