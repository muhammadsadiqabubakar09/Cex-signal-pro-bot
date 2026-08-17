import time
import requests
import pandas as pd


# ============================================================
# BINANCE MARKET DATA API — V2
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
    Fetch CLOSED OHLCV candles from Binance.

    V2 improvements:
        - Uses Binance market data endpoints
        - Retries failed requests
        - Validates returned data
        - Converts numeric fields safely
        - Sorts candles chronologically
        - Removes duplicate candles
        - Removes the CURRENT OPEN CANDLE
        - Returns CLOSED candles only

    This is important because indicators and SMC
    should not calculate signals from a candle
    that is still forming.

    Returns:
        pandas.DataFrame
    """

    symbol = str(symbol).upper().strip()

    if not symbol:
        raise ValueError(
            "Symbol cannot be empty."
        )

    # --------------------------------------------------------
    # Validate limit
    # --------------------------------------------------------

    if limit < 50:
        limit = 50

    if limit > 1000:
        limit = 1000

    # --------------------------------------------------------
    # Request slightly more candles.
    #
    # We request one extra candle because the newest
    # candle may still be open and will be removed.
    # --------------------------------------------------------

    request_limit = min(
        limit + 1,
        1000
    )

    params = {
        "symbol": symbol,
        "interval": interval,
        "limit": request_limit
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
                        f"No candle data returned for "
                        f"{symbol} {interval}."
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
                # SORT + REMOVE DUPLICATES
                # ====================================================

                df = (
                    df
                    .sort_values("time")
                    .drop_duplicates(
                        subset=["time"]
                    )
                    .reset_index(drop=True)
                )

                # ====================================================
                # REMOVE CURRENT OPEN CANDLE
                # ====================================================

                current_time_ms = int(
                    time.time() * 1000
                )

                df = df[
                    df["close_time"] < current_time_ms
                ].reset_index(
                    drop=True
                )

                # ====================================================
                # FINAL DATA LIMIT
                # ====================================================

                if len(df) > limit:

                    df = df.tail(
                        limit
                    ).reset_index(
                        drop=True
                    )

                # ====================================================
                # FINAL VALIDATION
                # ====================================================

                if len(df) < 50:

                    raise ValueError(
                        f"Insufficient CLOSED candle data "
                        f"for {symbol} {interval}: "
                        f"{len(df)} candles."
                    )

                # ====================================================
                # SAFETY CHECK
                # ====================================================

                newest_close_time = int(
                    df["close_time"].iloc[-1]
                )

                if newest_close_time >= current_time_ms:

                    raise ValueError(
                        "Current candle was not removed."
                    )

                # ====================================================
                # RETURN CLOSED CANDLES
                # ====================================================

                return df

            except Exception as error:

                last_error = error

                # ------------------------------------------------
                # Retry
                # ------------------------------------------------

                if attempt < MAX_RETRIES - 1:

                    time.sleep(1)

        # --------------------------------------------------------
        # Try fallback endpoint
        # --------------------------------------------------------

    # ========================================================
    # ALL ENDPOINTS FAILED
    # ========================================================

    raise Exception(
        f"Unable to download CLOSED candles for "
        f"{symbol} {interval}. "
        f"Last error: {last_error}"
    )