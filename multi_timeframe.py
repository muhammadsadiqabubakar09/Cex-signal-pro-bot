from binance_api import get_candles
from indicators import add_indicators

# ==========================================================
# TIMEFRAMES
# ==========================================================

TIMEFRAMES = [
    "5m",
    "15m",
    "1h",
    "4h",
    "1d"
]


def get_trend(last):
    """
    Detect overall trend using EMA alignment.
    """

    if (
        last["ema20"] > last["ema50"]
        and last["ema50"] > last["ema200"]
    ):
        return "BULLISH"

    elif (
        last["ema20"] < last["ema50"]
        and last["ema50"] < last["ema200"]
    ):
        return "BEARISH"

    return "NEUTRAL"


def analyze_timeframe(symbol, interval):
    """
    Analyze a single timeframe.
    """

    try:

        df = get_candles(symbol, interval)

        if df is None or df.empty:
            return None

        df = add_indicators(df)

        if df is None or df.empty:
            return None

        last = df.iloc[-1]

        volume_ratio = 1.0

        if last["volume_sma"] > 0:
            volume_ratio = (
                last["volume"] /
                last["volume_sma"]
            )

        return {

            # =====================
            # PRICE
            # =====================

            "close": last["close"],

            # =====================
            # TREND
            # =====================

            "trend": get_trend(last),

            # =====================
            # EMA
            # =====================

            "ema20": last["ema20"],
            "ema50": last["ema50"],
            "ema200": last["ema200"],

            "ema_alignment":

                last["ema20"] >
                last["ema50"] >
                last["ema200"],

            # =====================
            # RSI
            # =====================

            "rsi": last["rsi"],

            # =====================
            # STOCH RSI
            # =====================

            "stoch_rsi": last["stoch_rsi"],
            "stoch_rsi_k": last["stoch_rsi_k"],
            "stoch_rsi_d": last["stoch_rsi_d"],

            # =====================
            # MACD
            # =====================

            "macd": last["macd"],
            "macd_signal": last["macd_signal"],
            "macd_hist": last["macd_hist"],

            # =====================
            # ADX
            # =====================

            "adx": last["adx"],

            # =====================
            # ATR
            # =====================

            "atr": last["atr"],

            # =====================
            # BOLLINGER
            # =====================

            "bb_upper": last["bb_upper"],
            "bb_middle": last["bb_middle"],
            "bb_lower": last["bb_lower"],
            "bb_width": last["bb_width"],

            # =====================
            # VWAP
            # =====================

            "vwap": last["vwap"],

            # =====================
            # VOLUME
            # =====================

            "volume": last["volume"],
            "volume_sma": last["volume_sma"],
            "volume_ratio": round(volume_ratio, 2)
        }

    except Exception:
        return None


def analyze_symbol(symbol):
    """
    Analyze all configured timeframes.
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