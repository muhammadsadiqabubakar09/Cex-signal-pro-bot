from watchlist import get_watchlist
from multi_timeframe import analyze_symbol
from signals import generate_signal
from risk_manager import calculate_trade
from formatter import format_signal
from logger import log_info, log_warning, log_error

MIN_SCORE = 80


def scan_symbol(symbol):

    try:

        log_info(f"Scanning {symbol}")

        mtf_data = analyze_symbol(symbol)

        if mtf_data is None:
            log_warning(f"No market data for {symbol}")
            return None

        signal_data = generate_signal(mtf_data)

        if signal_data["score"] < MIN_SCORE:
            return None

        price = mtf_data["5m"]["close"]
        atr = mtf_data["5m"]["atr"]

        risk_data = calculate_trade(
            price,
            atr,
            signal_data
        )

        message = format_signal(
            symbol,
            signal_data,
            risk_data
        )

        return {
            "symbol": symbol,
            "score": signal_data["score"],
            "message": message
        }

    except Exception as e:

        log_error(f"{symbol}: {e}")

        return None


def scan_market():

    watchlist = get_watchlist()

    results = []

    for symbol in watchlist:

        result = scan_symbol(symbol)

        if result:
            results.append(result)

    results.sort(
        key=lambda x: x["score"],
        reverse=True
    )

    return results[:5]