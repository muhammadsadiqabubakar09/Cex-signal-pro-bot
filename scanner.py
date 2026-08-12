from watchlist import get_watchlist
from multi_timeframe import analyze_symbol
from signals import generate_signal
from risk_manager import calculate_trade
from formatter import format_signal
from logger import log_info, log_error

import traceback

# Prevent duplicate signals
SENT_SIGNALS = set()


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

    signal_id = (
        symbol,
        signal_data["direction"],
        round(price, 6)
    )

    return signal_id, message


def scan_market():
    """
    Manual scan.
    Returns only new signals.
    """

    watchlist = get_watchlist()

    results = []

    log_info(f"Scanning {len(watchlist)} symbols...")

    for symbol in watchlist:

        try:

            result = scan_symbol(symbol)

            if result is None:
                continue

            signal_id, message = result

            if signal_id in SENT_SIGNALS:
                continue

            SENT_SIGNALS.add(signal_id)

            results.append(message)

        except Exception:

            log_error(
                f"Error while scanning {symbol}\n"
                + traceback.format_exc()
            )

    log_info(
        f"Scan completed. {len(results)} new signal(s)."
    )

    return results


def auto_scan():
    """
    Auto scan every 5 minutes.
    """

    return scan_market()