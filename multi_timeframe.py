from binance_api import get_candles
from indicators import add_indicators
from smc import analyze_smc


# ============================================================
# TIMEFRAME CONFIGURATION
# ============================================================

TIMEFRAMES = [
    "5m",
    "15m",
    "1h",
    "4h",
    "1d"
]

CANDLE_LIMIT = 250


# ============================================================
# ANALYZE ONE TIMEFRAME
# ============================================================

def analyze_timeframe(
    symbol,
    interval
):
    """
    Analyze one timeframe.

    Pipeline:

        Binance
           ↓
        Candles
           ↓
        Indicators
           ↓
        SMC
           ↓
        Timeframe data

    Output is compatible with signals.py.
    """

    try:

        # ----------------------------------------------------
        # Get Binance candles
        # ----------------------------------------------------

        df = get_candles(
            symbol,
            interval,
            CANDLE_LIMIT
        )

        if df is None or df.empty:
            return None

        # ----------------------------------------------------
        # Add technical indicators
        # ----------------------------------------------------

        df = add_indicators(
            df
        )

        if df is None or df.empty:
            return None

        # ----------------------------------------------------
        # Make sure required indicators exist
        # ----------------------------------------------------

        required_indicators = [
            "ema20",
            "ema50",
            "ema200",
            "rsi",
            "stoch_rsi",
            "stoch_rsi_k",
            "stoch_rsi_d",
            "macd",
            "macd_signal",
            "macd_hist",
            "adx",
            "atr",
            "bb_upper",
            "bb_middle",
            "bb_lower",
            "bb_width",
            "vwap",
            "volume",
            "volume_sma"
        ]

        for column in required_indicators:

            if column not in df.columns:
                return None

        # ----------------------------------------------------
        # SMC
        # ----------------------------------------------------

        smc_data = analyze_smc(
            df
        )

        if smc_data is None:
            return None

        # ----------------------------------------------------
        # Latest candle
        # ----------------------------------------------------

        last = df.iloc[-1]

        # ----------------------------------------------------
        # Validate latest candle
        # ----------------------------------------------------

        values = [
            last["close"],
            last["ema20"],
            last["ema50"],
            last["ema200"],
            last["rsi"],
            last["stoch_rsi"],
            last["stoch_rsi_k"],
            last["stoch_rsi_d"],
            last["macd"],
            last["macd_signal"],
            last["macd_hist"],
            last["adx"],
            last["atr"],
            last["bb_upper"],
            last["bb_middle"],
            last["bb_lower"],
            last["bb_width"],
            last["vwap"],
            last["volume"],
            last["volume_sma"]
        ]

        for value in values:

            if value is None:
                return None

        # ----------------------------------------------------
        # Return timeframe data
        # ----------------------------------------------------

        return {

            "close":
                float(last["close"]),

            "ema20":
                float(last["ema20"]),

            "ema50":
                float(last["ema50"]),

            "ema200":
                float(last["ema200"]),

            "rsi":
                float(last["rsi"]),

            "stoch_rsi":
                float(last["stoch_rsi"]),

            "stoch_rsi_k":
                float(last["stoch_rsi_k"]),

            "stoch_rsi_d":
                float(last["stoch_rsi_d"]),

            "macd":
                float(last["macd"]),

            "macd_signal":
                float(last["macd_signal"]),

            "macd_hist":
                float(last["macd_hist"]),

            "adx":
                float(last["adx"]),

            "atr":
                float(last["atr"]),

            "bb_upper":
                float(last["bb_upper"]),

            "bb_middle":
                float(last["bb_middle"]),

            "bb_lower":
                float(last["bb_lower"]),

            "bb_width":
                float(last["bb_width"]),

            "vwap":
                float(last["vwap"]),

            "volume":
                float(last["volume"]),

            "volume_sma":
                float(last["volume_sma"]),

            "smc":
                smc_data
        }

    except Exception:

        return None


# ============================================================
# ANALYZE COMPLETE SYMBOL
# ============================================================

def analyze_symbol(symbol):
    """
    Analyze all required timeframes.

    Required:

        5m
        15m
        1h
        4h
        1d

    Returns None if any required timeframe fails.

    This prevents signals.py from receiving incomplete
    multi-timeframe data.
    """

    result = {}

    for timeframe in TIMEFRAMES:

        data = analyze_timeframe(
            symbol,
            timeframe
        )

        if data is None:
            return None

        result[timeframe] = data

    return result