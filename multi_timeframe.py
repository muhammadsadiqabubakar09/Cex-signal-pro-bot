from binance_api import get_candles
from indicators import add_indicators


TIMEFRAMES = [
    "5m",
    "15m",
    "1h"
]


def analyze_timeframe(symbol, interval):

    df = get_candles(symbol, interval)

    df = add_indicators(df)

    last = df.iloc[-1]

    return {
        "timeframe": interval,
        "ema20": last["ema20"],
        "ema50": last["ema50"],
        "rsi": last["rsi"],
        "price": last["close"],
    }


def analyze_symbol(symbol):

    result = {}

    for tf in TIMEFRAMES:

        result[tf] = analyze_timeframe(symbol, tf)

    return result
