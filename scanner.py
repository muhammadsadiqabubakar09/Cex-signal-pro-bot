from binance_api import get_candles
from indicators import add_indicators, analyze


def scan(symbol):

    df = get_candles(symbol)

    df = add_indicators(df)

    result = analyze(df)

    if result:
        result["symbol"] = symbol
        result["price"] = round(df.iloc[-1]["close"], 4)

    return result


def scan_all(symbols):

    signals = []

    for symbol in symbols:

        signal = scan(symbol)

        if signal:
            signals.append(signal)

    return signals
