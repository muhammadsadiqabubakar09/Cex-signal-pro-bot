import requests
import pandas as pd

PRIMARY_URL = "https://data-api.binance.vision/api/v3/klines"
FALLBACK_URL = "https://api.binance.com/api/v3/klines"


def get_candles(symbol, interval="15m", limit=200):
    """
    Fetch OHLCV candle data from Binance with automatic fallback.
    """

    params = {
        "symbol": symbol,
        "interval": interval,
        "limit": limit
    }

    data = None

    for url in [PRIMARY_URL, FALLBACK_URL]:

        try:

            response = requests.get(
                url,
                params=params,
                timeout=10
            )

            response.raise_for_status()

            data = response.json()

            if data:
                break

        except Exception:
            continue

    if not data:
        raise Exception(
            f"Unable to download candle data for {symbol}"
        )

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