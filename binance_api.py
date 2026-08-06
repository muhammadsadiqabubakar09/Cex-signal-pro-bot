import requests
import pandas as pd

BASE_URL = "https://api.binance.com/api/v3/klines"


def get_candles(symbol, interval="15m", limit=200):

    params = {
        "symbol": symbol,
        "interval": interval,
        "limit": limit
    }

    response = requests.get(BASE_URL, params=params, timeout=10)
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
        "quote_volume",
        "trades",
        "tb_base",
        "tb_quote",
        "ignore"
    ])

    numeric = [
        "open",
        "high",
        "low",
        "close",
        "volume"
    ]

    for col in numeric:
        df[col] = df[col].astype(float)

    return df