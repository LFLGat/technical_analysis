from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
import yfinance as yf
import pandas as pd
import numpy as np
from scipy.signal import find_peaks
import plotly.graph_objects as go
import plotly.utils
import json

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

def fetch_data(ticker, start_date, end_date, interval):
    data = yf.download(ticker, start=start_date, end=end_date, interval=interval)
    if interval == "1m":
        # Filter to market hours only (9 AM to 4 PM)
        data = data.between_time("09:00", "16:00")
    return data

@app.get("/", response_class=HTMLResponse)
async def read_form(request: Request):
    return templates.TemplateResponse("form.html", {"request": request})

@app.post("/plot/", response_class=JSONResponse)
async def plot_significant_levels(
    stock_ticker: str = Form(...),
    start_date: str = Form(...),
    end_date: str = Form(...)
):
    data_1m = fetch_data(stock_ticker, start_date, end_date, "1m")
    if data_1m.empty:
        return JSONResponse(status_code=404, content={"message": "No data found for the given parameters."})

    significant_levels_1m = find_significant_levels(data_1m)

    fig = go.Figure(data=[go.Candlestick(
        x=data_1m.index,
        open=data_1m['Open'],
        high=data_1m['High'],
        low=data_1m['Low'],
        close=data_1m['Close']
    )])

    for level in significant_levels_1m:
        fig.add_hline(y=level, line=dict(color='yellow', dash='dash'))

    fig.update_layout(title=f'{stock_ticker} Significant Levels', yaxis_title='Price', xaxis_title='Time')

    graphJSON = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
    return JSONResponse(content={"graphJSON": graphJSON})
