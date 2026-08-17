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
# SIGNAL QUALITY CONFIGURATION
# ============================================================

MIN_SIGNAL_SCORE = 80

MIN_RISK_REWARD = 2.0

# Avoid sending a trade when price is already too extended
# from its short-term mean.
MAX_ATR_EXTENSION = 2.5


# ============================================================
# SIGNAL ID
# ============================================================

def create_signal_id(
    symbol,
    signal_data,
    risk_data
):
    """
    Create a stable identity for a trade setup.

    The setup identity includes direction, confidence
    and entry zone characteristics.
    """

    entry = round(
        float(
            risk_data.get(
                "entry",
                0
            )
        ),
        8
    )

    return (
        symbol,
        signal_data.get("direction"),
        signal_data.get("market"),
        signal_data.get("confidence"),
        entry
    )


# ============================================================
# DUPLICATE CHECK
# ============================================================

def is_duplicate(signal_id):
    """
    Check whether the same setup was recently sent.
    """

    current_time = time.time()

    last_sent = SENT_SIGNALS.get(
        signal_id
    )

    if last_sent is None:
        return False

    return (
        current_time - last_sent
        < SIGNAL_COOLDOWN
    )


# ============================================================
# SAVE SIGNAL
# ============================================================

def remember_signal(signal_id):
    """
    Remember when a signal was sent.
    """

    SENT_SIGNALS[
        signal_id
    ] = time.time()


# ============================================================
# CLEAN OLD SIGNALS
# ============================================================

def cleanup_old_signals():
    """
    Remove expired signal records.
    """

    current_time = time.time()

    expired = []

    for signal_id, timestamp in list(
        SENT_SIGNALS.items()
    ):

        if (
            current_time - timestamp
            >= SIGNAL_COOLDOWN
        ):

            expired.append(
                signal_id
            )

    for signal_id in expired:

        SENT_SIGNALS.pop(
            signal_id,
            None
        )


# ============================================================
# SIGNAL QUALITY VALIDATION
# ============================================================

def validate_signal_quality(
    signal_data,
    risk_data,
    mtf_data
):
    """
    Final quality gate before a signal is sent.

    This is intentionally stricter than signals.py.

    The signal engine determines direction.

    The scanner determines whether the resulting
    trade is good enough to actually send.
    """

    if not signal_data:
        return False

    if not risk_data:
        return False

    # --------------------------------------------------------
    # Score
    # --------------------------------------------------------

    score = float(
        signal_data.get(
            "score",
            0
        )
    )

    if score < MIN_SIGNAL_SCORE:

        log_info(
            f"Signal rejected: score too low "
            f"({score})"
        )

        return False

    # --------------------------------------------------------
    # Direction
    # --------------------------------------------------------

    direction = signal_data.get(
        "direction"
    )

    if direction not in [
        "BUY",
        "LONG",
        "SHORT"
    ]:

        return False

    # --------------------------------------------------------
    # Risk / Reward
    # --------------------------------------------------------

    risk_reward = float(
        risk_data.get(
            "risk_reward",
            0
        )
    )

    if risk_reward < MIN_RISK_REWARD:

        log_info(
            f"Signal rejected: insufficient RR "
            f"({risk_reward})"
        )

        return False

    # --------------------------------------------------------
    # Price validation
    # --------------------------------------------------------

    tf5 = mtf_data.get(
        "5m"
    )

    if not tf5:
        return False

    entry = float(
        risk_data.get(
            "entry",
            0
        )
    )

    atr = float(
        tf5.get(
            "atr",
            0
        )
    )

    if entry <= 0 or atr <= 0:
        return False

    # ========================================================
    # EXTENSION FILTER
    # ========================================================

    ema20 = float(
        tf5.get(
            "ema20",
            entry
        )
    )

    extension = abs(
        entry - ema20
    ) / atr

    if extension > MAX_ATR_EXTENSION:

        log_info(
            f"Signal rejected: price too extended "
            f"({extension:.2f} ATR)"
        )

        return False

    # ========================================================
    # FINAL VALIDATION
    # ========================================================

    return True


# ============================================================
# SCAN ONE SYMBOL
# ============================================================

def scan_symbol(symbol):
    """
    Scan a single symbol.

    Pipeline:

        Binance
            ↓
        Indicators
            ↓
        SMC
            ↓
        Multi-Timeframe Analysis
            ↓
        Signal Engine
            ↓
        Quality Gate
            ↓
        Risk Manager
            ↓
        Duplicate Protection
            ↓
        Formatter
    """

    # ========================================================
    # MULTI-TIMEFRAME ANALYSIS
    # ========================================================

    mtf_data = analyze_symbol(
        symbol
    )

    if mtf_data is None:

        log_info(
            f"{symbol} | "
            f"Rejected: incomplete market data"
        )

        return None

    # ========================================================
    # GENERATE SIGNAL
    # ========================================================

    signal_data = generate_signal(
        mtf_data
    )

    if not signal_data:

        return None

    # ========================================================
    # DEBUG LOGGING
    # ========================================================

    log_info(
        f"{symbol} | "
        f"Score={signal_data.get('score', 0)} | "
        f"Direction={signal_data.get('direction')} | "
        f"Signal={signal_data.get('signal')}"
    )

    # ========================================================
    # DIRECTION VALIDATION
    # ========================================================

    if signal_data.get(
        "direction"
    ) == "NONE":

        return None

    # ========================================================
    # 5M MARKET DATA
    # ========================================================

    tf5 = mtf_data.get(
        "5m"
    )

    if not tf5:

        return None

    try:

        price = float(
            tf5["close"]
        )

        atr = float(
            tf5["atr"]
        )

    except (
        KeyError,
        TypeError,
        ValueError
    ):

        return None

    if price <= 0 or atr <= 0:

        return None

    # ========================================================
    # RISK CALCULATION
    # ========================================================

    risk_data = calculate_trade(
        price,
        atr,
        signal_data
    )

    if not risk_data:

        log_info(
            f"{symbol} | "
            f"Rejected by risk manager"
        )

        return None

    # ========================================================
    # FINAL QUALITY GATE
    # ========================================================

    if not validate_signal_quality(
        signal_data,
        risk_data,
        mtf_data
    ):

        return None

    # ========================================================
    # DUPLICATE PROTECTION
    # ========================================================

    signal_id = create_signal_id(
        symbol,
        signal_data,
        risk_data
    )

    if is_duplicate(
        signal_id
    ):

        log_info(
            f"{symbol} | "
            f"Duplicate signal ignored"
        )

        return None

    # ========================================================
    # FORMAT MESSAGE
    # ========================================================

    message = format_signal(
        symbol,
        signal_data,
        risk_data
    )

    if not message:

        return None

    # ========================================================
    # REMEMBER SIGNAL
    # ========================================================

    remember_signal(
        signal_id
    )

    log_info(
        f"{symbol} | "
        f"VALID SIGNAL SENT | "
        f"Score={signal_data.get('score')} | "
        f"RR={risk_data.get('risk_reward')}"
    )

    return (
        signal_id,
        message
    )


# ============================================================
# MARKET SCANNER
# ============================================================

def scan_market():
    """
    Scan the complete watchlist.

    Only signals that pass:

        1. Complete MTF data
        2. Signal engine
        3. Minimum score
        4. Risk manager
        5. Minimum RR
        6. Extension filter
        7. Duplicate protection

    are returned.
    """

    cleanup_old_signals()

    watchlist = get_watchlist()

    if not watchlist:

        log_info(
            "Watchlist is empty."
        )

        return []

    results = []

    log_info(
        f"Starting market scan | "
        f"{len(watchlist)} symbols"
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
        f"Scan completed | "
        f"{len(results)} valid signal(s)"
    )

    return results


# ============================================================
# AUTO SCAN
# ============================================================

def auto_scan():
    """
    Auto-scan entry point.

    main.py controls the actual schedule.

    Every scan passes through the same quality
    validation pipeline.
    """

    try:

        return scan_market()

    except Exception:

        log_error(
            "Critical auto-scan error\n"
            + traceback.format_exc()
        )

        return []