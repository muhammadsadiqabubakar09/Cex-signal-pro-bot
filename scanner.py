from watchlist import get_watchlist
from multi_timeframe import analyze_symbol
from signals import generate_signal
from risk_manager import calculate_trade
from formatter import format_signal


def scan_symbol(symbol):
    """
    Scan a single symbol and return formatted signal.
    """

    mtf_data = analyze_symbol(symbol)

    if mtf_data is None:
        return None

    signal_data = generate_signal(mtf_data)

    if signal_data["direction"] == "NONE":
        return None

    price = mtf_data["5m"]["close"]
    atr = mtf_data["5m"]["atr"]

    risk_data = calculate_trade(
        price,
        atr,
        signal_data
    )

    if not risk_data:
        return None

    message = format_signal(
        symbol,
        signal_data,
        risk_data
    )

    return message


def scan_market():
    """
    Scan all watchlist coins.
    """

    watchlist = get_watchlist()

    signals = []

    for symbol in watchlist:

        try:

            message = scan_symbol(symbol)

            if message:
                signals.append(message)

        except Exception as e:

            print(f"{symbol}: {e}")

    return signals