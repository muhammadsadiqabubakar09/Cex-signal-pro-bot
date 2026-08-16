import requests
import pandas as pd


# ============================================================
# BINANCE API CONFIGURATION
# ============================================================

PRIMARY_URL = "https://data-api.binance.vision/api/v3/klines"
FALLBACK_URL = "https://api.binance.com/api/v3/klines"

REQUEST_TIMEOUT = 10
DEFAULT_LIMIT = 250


# ============================================================
# GET CANDLES
# ============================================================

def get_candles(
    symbol,
    interval="15m",
    limit=DEFAULT_LIMIT
):
    """
    Download OHLCV candle data from Binance.

    Primary endpoint is tried first.
    If it fails, the standard Binance API is used.

    Returns:
        pandas.DataFrame
    """

    params = {
        "symbol": symbol.upper(),
        "interval": interval,
        "limit": limit
    }

    last_error = None

    for url in [PRIMARY_URL, FALLBACK_URL]:

        try:

            response = requests.get(
                url,
                params=params,
                timeout=REQUEST_TIMEOUT
            )

            response.raise_for_status()

            data = response.json()

            if not isinstance(data, list) or not data:
                continue

            df = pd.DataFrame(
                data,
                columns=[
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
                ]
            )

            # ------------------------------------------------
            # Convert numeric market data
            # ------------------------------------------------

            numeric_columns = [
                "open",
                "high",
                "low",
                "close",
                "volume"
            ]

            for column in numeric_columns:

                df[column] = pd.to_numeric(
                    df[column],
                    errors="coerce"
                )

            # ------------------------------------------------
            # Clean invalid rows
            # ------------------------------------------------

            df = df.dropna(
                subset=numeric_columns
            )

            df = df.sort_values(
                "time"
            ).reset_index(
                drop=True
            )

            if df.empty:
                continue

            return df

        except Exception as error:

            last_error = error
            continue

    raise Exception(
        f"Unable to download candles for "
        f"{symbol} {interval}. "
        f"Last error: {last_error}"
    )