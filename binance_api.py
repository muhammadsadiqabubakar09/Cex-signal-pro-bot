import requests
import pandas as pd
import time


# ============================================================
# BINANCE MARKET DATA API
# ============================================================

PRIMARY_URL = "https://data-api.binance.vision/api/v3/klines"
FALLBACK_URL = "https://api.binance.com/api/v3/klines"

REQUEST_TIMEOUT = 10
DEFAULT_LIMIT = 250
MAX_RETRIES = 2


# ============================================================
# GET CANDLES
# ============================================================

def get_candles(
    symbol,
    interval="15m",
    limit=DEFAULT_LIMIT
):
    """
    Fetch OHLCV candle data from Binance.

    Features:
        - Primary Binance data endpoint
        - Automatic fallback endpoint
        - Retry protection
        - Data validation
        - Numeric conversion
        - Chronological sorting

    Returns:
        pandas.DataFrame
    """

    symbol = str(symbol).upper().strip()

    if not symbol:
        raise ValueError("Symbol cannot be empty.")

    if limit < 50:
        limit = 50

    if limit > 1000:
        limit = 1000

    params = {
        "symbol": symbol,
        "interval": interval,
        "limit": limit
    }

    urls = [
        PRIMARY_URL,
        FALLBACK_URL
    ]

    last_error = None

    # ========================================================
    # REQUEST LOOP
    # ========================================================

    for url in urls:

        for attempt in range(MAX_RETRIES):

            try:

                response = requests.get(
                    url,
                    params=params,
                    timeout=REQUEST_TIMEOUT
                )

                response.raise_for_status()

                data = response.json()

                # ------------------------------------------------
                # Validate Binance response
                # ------------------------------------------------

                if not isinstance(data, list):
                    raise ValueError(
                        "Binance returned an invalid response."
                    )

                if not data:
                    raise ValueError(
                        f"No candle data returned for {symbol} {interval}."
                    )

                # ------------------------------------------------
                # Create DataFrame
                # ------------------------------------------------

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

                # ====================================================
                # NUMERIC CONVERSION
                # ====================================================

                numeric_columns = [
                    "time",
                    "open",
                    "high",
                    "low",
                    "close",
                    "volume",
                    "close_time",
                    "quote_volume",
                    "trades"
                ]

                for column in numeric_columns:

                    df[column] = pd.to_numeric(
                        df[column],
                        errors="coerce"
                    )

                # ====================================================
                # REMOVE INVALID ROWS
                # ====================================================

                price_columns = [
                    "open",
                    "high",
                    "low",
                    "close",
                    "volume"
                ]

                df = df.dropna(
                    subset=price_columns
                )

                # ====================================================
                # REMOVE INVALID PRICES
                # ====================================================

                df = df[
                    (df["open"] > 0) &
                    (df["high"] > 0) &
                    (df["low"] > 0) &
                    (df["close"] > 0) &
                    (df["volume"] >= 0)
                ]

                # ====================================================
                # SORT CANDLES
                # ====================================================

                df = df.sort_values(
                    "time"
                ).drop_duplicates(
                    subset=["time"]
                ).reset_index(
                    drop=True
                )

                # ====================================================
                # FINAL VALIDATION
                # ====================================================

                if len(df) < 50:

                    raise ValueError(
                        f"Insufficient candle data for "
                        f"{symbol} {interval}: {len(df)} candles."
                    )

                return df

            except Exception as error:

                last_error = error

                # Retry only when another attempt is available
                if attempt < MAX_RETRIES - 1:
                    time.sleep(1)

        # Move to fallback endpoint

    # ========================================================
    # ALL ENDPOINTS FAILED
    # ========================================================

    raise Exception(
        f"Unable to download candles for "
        f"{symbol} {interval}. "
        f"Last error: {last_error}"
    )