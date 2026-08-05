import requests
import pandas as pd

BASE_URL = "https://api.binance.com"

def get_candles(symbol, interval="15m", limit=100):
    url = f"{BASE_URL}/api/v3/klines"

    params = {
        "symbol": symbol,
        "interval": interval,
        "limit": limit
    }

    response = requests.get(url, params=params, timeout=10)
    response.raise_for_status()

    data = response.json()

    df = pd.DataFrame(data, columns=[
        "time",
        "open",
        "high",
        "low",
        "close",
        "volume",
        "close_time",
        "quote_asset_volume",
        "number_of_trades",
        "taker_buy_base",
        "taker_buy_quote",
        "ignore"
    ])

    df["close"] = df["close"].astype(float)
    df["volume"] = df["volume"].astype(float)

    return df
