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
    data_5m = fetch_data(stock_ticker, start_date, end_date, "5m")
    data_15m = fetch_data(stock_ticker, start_date, end_date, "15m")
    data_1h = fetch_data(stock_ticker, start_date, end_date, "1h")

    if data_1m.empty or data_5m.empty or data_15m.empty or data_1h.empty:
        return JSONResponse(status_code=404, content={"message": "No data found for the given parameters."})

    significant_levels_1m = find_significant_levels(data_1m)
    valid_levels = find_significant_levels(data_1m)

    fig1 = go.Figure(data=[go.Candlestick(
        x=data_1m.index,
        open=data_1m['Open'],
        high=data_1m['High'],
        low=data_1m['Low'],
        close=data_1m['Close']
    )])
    fig2 = go.Figure(data=[go.Candlestick(
        x=data_5m.index,
        open=data_5m['Open'],
        high=data_5m['High'],
        low=data_5m['Low'],
        close=data_5m['Close']
    )])
    fig3 = go.Figure(data=[go.Candlestick(
        x=data_15m.index,
        open=data_15m['Open'],
        high=data_15m['High'],
        low=data_15m['Low'],
        close=data_15m['Close']
    )])
    fig4 = go.Figure(data=[go.Candlestick(
        x=data_1h.index,
        open=data_1h['Open'],
        high=data_1h['High'],
        low=data_1h['Low'],
        close=data_1h['Close']
    )])

    for level in significant_levels_1m:
        fig1.add_hline(y=level, line=dict(color='yellow', dash='dash'))
    for level in valid_levels:
        fig2.add_hline(y=level, line=dict(color='yellow', dash='dash'))
        fig3.add_hline(y=level, line=dict(color='yellow', dash='dash'))
        fig4.add_hline(y=level, line=dict(color='yellow', dash='dash'))

    for fig in [fig1, fig2, fig3, fig4]:
        fig.update_xaxes(
            rangeslider_visible=True,
            rangebreaks=[
                dict(bounds=["sat", "mon"]),  # Hide weekends
                dict(bounds=[16, 9.5], pattern="hour")  # Hide hours outside 9:30am-4pm
            ]
        )

    fig1.update_layout(title=f'{stock_ticker} - 1 Minute Interval', yaxis_title='Price', xaxis_title='Time')
    fig2.update_layout(title=f'{stock_ticker} - 5 Minute Interval', yaxis_title='Price', xaxis_title='Time')
    fig3.update_layout(title=f'{stock_ticker} - 15 Minute Interval', yaxis_title='Price', xaxis_title='Time')
    fig4.update_layout(title=f'{stock_ticker} - 1 Hour Interval', yaxis_title='Price', xaxis_title='Time')

    graphJSON1 = json.dumps(fig1, cls=plotly.utils.PlotlyJSONEncoder)
    graphJSON2 = json.dumps(fig2, cls=plotly.utils.PlotlyJSONEncoder)
    graphJSON3 = json.dumps(fig3, cls=plotly.utils.PlotlyJSONEncoder)
    graphJSON4 = json.dumps(fig4, cls=plotly.utils.PlotlyJSONEncoder)

    return JSONResponse(content={
        "graphJSON1": graphJSON1,
        "graphJSON2": graphJSON2,
        "graphJSON3": graphJSON3,
        "graphJSON4": graphJSON4
    })
