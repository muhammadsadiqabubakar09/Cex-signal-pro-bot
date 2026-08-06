from binance_api import get_candles
from indicators import add_indicators

TIMEFRAMES = ["5m", "15m", "1h"]


def analyze_timeframe(symbol, interval):

    df = get_candles(symbol, interval)
    df = add_indicators(df)

    last = df.iloc[-1]

    return {
        "close": last["close"],

        "ema20": last["ema20"],
        "ema50": last["ema50"],

        "rsi": last["rsi"],

        "macd": last["macd"],
        "macd_signal": last["macd_signal"],

        "adx": last["adx"],

        "atr": last["atr"],

        "bb_upper": last["bb_upper"],
        "bb_middle": last["bb_middle"],
        "bb_lower": last["bb_lower"],

        "volume": last["volume"],
        "volume_sma": last["volume_sma"]
    }


def analyze_symbol(symbol):

    result = {}

    for tf in TIMEFRAMES:
        result[tf] = analyze_timeframe(symbol, tf)

    return result


       