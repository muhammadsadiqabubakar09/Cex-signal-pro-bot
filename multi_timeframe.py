from binance_api import get_candles
from indicators import add_indicators
from smc import analyze_smc


# ============================================================
# TIMEFRAMES
# ============================================================

TIMEFRAMES = [
    "5m",
    "15m",
    "1h",
    "4h",
    "1d"
]


# ============================================================
# ANALYZE ONE TIMEFRAME
# ============================================================

def analyze_timeframe(symbol, interval):
    """
    Analyze one timeframe.

    Returns technical indicators + SMC data.
    """

    try:

        df = get_candles(
            symbol,
            interval
        )

        if df is None or df.empty:
            return None

        # Add technical indicators
        df = add_indicators(df)

        if df is None or df.empty:
            return None

        # Analyze Smart Money Concepts
        smc_data = analyze_smc(df)

        if smc_data is None:
            return None

        last = df.iloc[-1]

        return {

            # ==================================================
            # PRICE
            # ==================================================

            "close": float(last["close"]),

            # ==================================================
            # EMA
            # ==================================================

            "ema20": float(last["ema20"]),
            "ema50": float(last["ema50"]),
            "ema200": float(last["ema200"]),

            # ==================================================
            # RSI
            # ==================================================

            "rsi": float(last["rsi"]),

            # ==================================================
            # STOCHASTIC RSI
            # ==================================================

            "stoch_rsi": float(last["stoch_rsi"]),
            "stoch_rsi_k": float(last["stoch_rsi_k"]),
            "stoch_rsi_d": float(last["stoch_rsi_d"]),

            # ==================================================
            # MACD
            # ==================================================

            "macd": float(last["macd"]),
            "macd_signal": float(last["macd_signal"]),
            "macd_hist": float(last["macd_hist"]),

            # ==================================================
            # ADX
            # ==================================================

            "adx": float(last["adx"]),

            # ==================================================
            # ATR
            # ==================================================

            "atr": float(last["atr"]),

            # ==================================================
            # BOLLINGER BANDS
            # ==================================================

            "bb_upper": float(last["bb_upper"]),
            "bb_middle": float(last["bb_middle"]),
            "bb_lower": float(last["bb_lower"]),
            "bb_width": float(last["bb_width"]),

            # ==================================================
            # VWAP
            # ==================================================

            "vwap": float(last["vwap"]),

            # ==================================================
            # VOLUME
            # ==================================================

            "volume": float(last["volume"]),
            "volume_sma": float(last["volume_sma"]),

            # ==================================================
            # SMART MONEY CONCEPTS
            # ==================================================

            "smc": smc_data

        }

    except Exception:
        return None


# ============================================================
# ANALYZE ALL TIMEFRAMES
# ============================================================

def analyze_symbol(symbol):
    """
    Analyze all configured timeframes.

    Returns:
        {
            "5m": {...},
            "15m": {...},
            "1h": {...},
            "4h": {...},
            "1d": {...}
        }
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