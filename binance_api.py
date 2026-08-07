import requests
import pandas as pd

BASE_URL = "https://api.binance.com/api/v3/klines"


def get_candles(symbol, interval="15m", limit=200):
    """
    Fetch candlestick (OHLCV) data from Binance
    """

    params = {
        "symbol": symbol,
        "interval": interval,
        "limit": limit
    }

    response = requests.get(BASE_URL, params=params, timeout=10)
    response.raise_for_status()

    data = response.json()

    if not data:
        raise ValueError(f"No candle data returned for {symbol}")

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

    numeric_columns = [
        "open",
        "high",
        "low",
        "close",
        "volume"
    ]

    for col in numeric_columns:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    df = df.dropna()

    df = df.sort_values("time").reset_index(drop=True)

    return df