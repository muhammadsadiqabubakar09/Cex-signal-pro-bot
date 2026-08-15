import time
import traceback

from watchlist import get_watchlist
from multi_timeframe import analyze_symbol
from signals import generate_signal
from risk_manager import calculate_trade
from formatter import format_signal
from logger import log_info, log_error


# ============================================================
# SIGNAL MEMORY
# ============================================================

SENT_SIGNALS = {}

SIGNAL_COOLDOWN = 30 * 60  # 30 minutes


# ============================================================
# SIGNAL ID
# ============================================================

def create_signal_id(symbol, signal_data):
    """
    Create a stable identity for a signal setup.

    Price is intentionally NOT included so that a small
    price movement does not create a duplicate signal.
    """

    return (
        symbol,
        signal_data["direction"],
        signal_data["market"],
        signal_data["confidence"]
    )


# ============================================================
# DUPLICATE CHECK
# ============================================================

def is_duplicate(signal_id):
    """
    Check whether the same setup was recently sent.
    """

    current_time = time.time()

    last_sent = SENT_SIGNALS.get(signal_id)

    if last_sent is None:
        return False

    if current_time - last_sent < SIGNAL_COOLDOWN:
        return True

    return False


# ============================================================
# SAVE SIGNAL
# ============================================================

def remember_signal(signal_id):
    """
    Remember when a signal was sent.
    """

    SENT_SIGNALS[signal_id] = time.time()


# ============================================================
# CLEAN OLD SIGNALS
# ============================================================

def cleanup_old_signals():
    """
    Remove expired signal records.
    """

    current_time = time.time()

    expired = []

    for signal_id, timestamp in SENT_SIGNALS.items():

        if current_time - timestamp >= SIGNAL_COOLDOWN:
            expired.append(signal_id)

    for signal_id in expired:
        SENT_SIGNALS.pop(
            signal_id,
            None
        )


# ============================================================
# SCORE BREAKDOWN LOGGER
# ============================================================

def log_score_breakdown(symbol, signal_data):
    """
    Log detailed score breakdown for debugging.

    This does NOT change the signal calculation.
    """

    breakdown = signal_data.get(
        "score_breakdown",
        {}
    )

    trend = breakdown.get("trend", 0)
    setup = breakdown.get("setup", 0)
    entry = breakdown.get("entry", 0)
    smc = breakdown.get("smc", 0)
    momentum = breakdown.get("momentum", 0)
    confirmation = breakdown.get("confirmation", 0)

    log_info(
        f"{symbol} | "
        f"Score={signal_data['score']} | "
        f"Trend={trend} | "
        f"Setup={setup} | "
        f"Entry={entry} | "
        f"SMC={smc} | "
        f"Momentum={momentum} | "
        f"Confirmation={confirmation} | "
        f"Direction={signal_data['direction']} | "
        f"Signal={signal_data['signal']}"
    )


# ============================================================
# SCAN ONE SYMBOL
# ============================================================

def scan_symbol(symbol):
    """
    Scan a single symbol.

    Flow:

        Market Data
            ↓
        Indicators + SMC
            ↓
        Signal Engine
            ↓
        Score Breakdown
            ↓
        Risk Manager
            ↓
        Formatter
    """

    # --------------------------------------------------------
    # Multi-timeframe analysis
    # --------------------------------------------------------

    mtf_data = analyze_symbol(symbol)

    if mtf_data is None:
        log_error(
            f"{symbol} | Multi-timeframe analysis failed."
        )
        return None

    # --------------------------------------------------------
    # Generate signal
    # --------------------------------------------------------

    signal_data = generate_signal(
        mtf_data
    )

    if not signal_data:
        log_error(
            f"{symbol} | Signal generation returned no data."
        )
        return None

    # --------------------------------------------------------
    # Detailed score logging
    # --------------------------------------------------------

    log_score_breakdown(
        symbol,
        signal_data
    )

    # --------------------------------------------------------
    # Ignore NO TRADE
    # --------------------------------------------------------

    if signal_data["direction"] == "NONE":
        return None

    # --------------------------------------------------------
    # Current 5M price and ATR
    # --------------------------------------------------------

    tf5 = mtf_data["5m"]

    price = float(
        tf5["close"]
    )

    atr = float(
        tf5["atr"]
    )

    # --------------------------------------------------------
    # Risk calculation
    # --------------------------------------------------------

    risk_data = calculate_trade(
        price,
        atr,
        signal_data
    )

    if not risk_data:
        return None

    # --------------------------------------------------------
    # Duplicate protection
    # --------------------------------------------------------

    signal_id = create_signal_id(
        symbol,
        signal_data
    )

    if is_duplicate(signal_id):
        return None

    # --------------------------------------------------------
    # Format message
    # --------------------------------------------------------

    message = format_signal(
        symbol,
        signal_data,
        risk_data
    )

    if not message:
        return None

    # --------------------------------------------------------
    # Remember signal
    # --------------------------------------------------------

    remember_signal(
        signal_id
    )

    return signal_id, message


# ============================================================
# MARKET SCANNER
# ============================================================

def scan_market():
    """
    Scan the complete watchlist.

    Returns only new valid signals.
    """

    cleanup_old_signals()

    watchlist = get_watchlist()

    results = []

    log_info(
        f"Scanning {len(watchlist)} symbols..."
    )

    for symbol in watchlist:

        try:

            result = scan_symbol(
                symbol
            )

            if result is None:
                continue

            signal_id, message = result

            results.append(
                message
            )

        except Exception:

            log_error(
                f"Error while scanning {symbol}\n"
                + traceback.format_exc()
            )

    log_info(
        f"Scan completed. "
        f"{len(results)} new signal(s)."
    )

    return results


# ============================================================
# AUTO SCAN
# ============================================================

def auto_scan():
    """
    Auto scan entry point.

    main.py controls the actual 5-minute schedule.
    """

    return scan_market()