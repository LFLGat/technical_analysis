from fastapi import FastAPI
import yfinance as yf
import pandas as pd
import mplfinance as mpf
import numpy as np
import matplotlib.pyplot as plt
from scipy.signal import find_peaks
from fastapi.responses import JSONResponse

app = FastAPI()

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
    return yf.download(ticker, start=start_date, end=end_date, interval=interval)

@app.get("/significant-levels/")
def get_significant_levels(ticker: str, start_date: str, end_date: str, interval: str):
    data = fetch_data(ticker, start_date, end_date, interval)
    if data.empty:
        return JSONResponse(status_code=404, content={"message": "No data found for the given parameters."})
    significant_levels = find_significant_levels(data)
    return {"significant_levels": significant_levels}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
