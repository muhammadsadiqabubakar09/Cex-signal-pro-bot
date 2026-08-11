from watchlist import get_watchlist
from multi_timeframe import analyze_symbol
from signals import generate_signal
from risk_manager import calculate_trade
from formatter import format_signal
from logger import log_info, log_error

import traceback


def scan_symbol(symbol):
    """
    Scan a single symbol and return a formatted signal.
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

    return format_signal(
        symbol,
        signal_data,
        risk_data
    )


def scan_market():
    """
    Scan all watchlist coins.
    """

    watchlist = get_watchlist()

    results = []

    log_info(f"Scanning {len(watchlist)} symbols...")

    for symbol in watchlist:

        try:

            message = scan_symbol(symbol)

            if message:
                results.append(message)

        except Exception:

            log_error(
                f"Error while scanning {symbol}\n"
                + traceback.format_exc()
            )

    log_info(
        f"Scan completed. {len(results)} signal(s) found."
    )

    return results