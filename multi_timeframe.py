from binance_api import get_candles
from indicators import add_indicators

TIMEFRAMES = ["5m", "15m", "1h"]


def analyze_timeframe(symbol, interval):
    """
    Analyze one timeframe.
    """

    df = get_candles(symbol, interval)
    df = add_indicators(df)

    last = df.iloc[-1]

    return {
        "close": last["close"],

        "ema20": last["ema20"],
        "ema50": last["ema50"],
        "ema200": last["ema200"],

        "rsi": last["rsi"],
        "stoch_rsi": last["stoch_rsi"],

        "macd": last["macd"],
        "macd_signal": last["macd_signal"],

        "adx": last["adx"],
        "atr": last["atr"],

        "bb_upper": last["bb_upper"],
        "bb_middle": last["bb_middle"],
        "bb_lower": last["bb_lower"],

        "vwap": last["vwap"],

        "volume": last["volume"],
        "volume_sma": last["volume_sma"]
    }


def analyze_symbol(symbol):
    """
    Analyze all configured timeframes.
    """

    results = {}

    for timeframe in TIMEFRAMES:
        try:
            results[timeframe] = analyze_timeframe(symbol, timeframe)
        except Exception as e:
            print(f"Error analyzing {symbol} ({timeframe}): {e}")

    return results