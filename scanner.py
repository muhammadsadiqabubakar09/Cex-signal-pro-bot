import time
import traceback

from watchlist import get_watchlist
from multi_timeframe import analyze_symbol
from signals import generate_signal
from risk_manager import calculate_trade
from formatter import format_signal
from logger import log_info, log_error


# ============================================================
# SCANNER CONFIGURATION
# ============================================================

# Same setup cannot generate another alert during this period.
SIGNAL_COOLDOWN = 30 * 60


# Maximum distance allowed between current price and
# calculated entry, measured in ATR.
#
# Example:
# ATR = 0.0010
# Maximum drift = 0.0005
#
# This prevents the bot from sending an entry after price
# has already moved too far.
MAX_ENTRY_DRIFT_ATR = 0.50


# Minimum ATR as percentage of current price.
#
# This helps reject extremely dead/low-volatility markets.
MIN_ATR_PERCENT = 0.10


# ============================================================
# SIGNAL MEMORY
# ============================================================

SENT_SIGNALS = {}


# ============================================================
# CREATE SIGNAL ID
# ============================================================

def create_signal_id(
    symbol,
    signal_data
):
    """
    Create a stable identity for a signal setup.

    Price is intentionally excluded because small price
    movements should not create duplicate signals.
    """

    return (
        symbol,
        signal_data.get("direction"),
        signal_data.get("market"),
        signal_data.get("confidence")
    )


# ============================================================
# DUPLICATE CHECK
# ============================================================

def is_duplicate(
    signal_id
):
    """
    Check whether this exact signal setup was recently sent.
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
# REMEMBER SIGNAL
# ============================================================

def remember_signal(
    signal_id
):
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
    Remove expired signal records from memory.
    """

    current_time = time.time()

    expired = []

    for signal_id, timestamp in SENT_SIGNALS.items():

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
# VALIDATE SIGNAL DATA
# ============================================================

def validate_signal_data(
    signal_data
):
    """
    Validate the basic structure of the signal engine output.
    """

    if not isinstance(
        signal_data,
        dict
    ):
        return False

    direction = signal_data.get(
        "direction"
    )

    market = signal_data.get(
        "market"
    )

    score = signal_data.get(
        "score"
    )

    confidence = signal_data.get(
        "confidence"
    )

    # --------------------------------------------------------
    # Direction
    # --------------------------------------------------------

    if direction not in [
        "BUY",
        "LONG",
        "SHORT"
    ]:

        return False

    # --------------------------------------------------------
    # Market
    # --------------------------------------------------------

    if market not in [
        "SPOT",
        "FUTURES"
    ]:

        return False

    # --------------------------------------------------------
    # Score
    # --------------------------------------------------------

    if not isinstance(
        score,
        (int, float)
    ):

        return False

    if score <= 0:

        return False

    # --------------------------------------------------------
    # Confidence
    # --------------------------------------------------------

    if confidence not in [
        "MEDIUM",
        "HIGH",
        "VERY HIGH"
    ]:

        return False

    return True


# ============================================================
# MARKET QUALITY CHECK
# ============================================================

def valid_market_conditions(
    tf5
):
    """
    Check whether the current 5M market has enough
    volatility to justify a trade.
    """

    try:

        close = float(
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

        return False

    # --------------------------------------------------------
    # Basic validation
    # --------------------------------------------------------

    if close <= 0:

        return False

    if atr <= 0:

        return False

    # --------------------------------------------------------
    # ATR percentage
    # --------------------------------------------------------

    atr_percent = (
        atr / close
    ) * 100

    # --------------------------------------------------------
    # Reject dead market
    # --------------------------------------------------------

    if atr_percent < MIN_ATR_PERCENT:

        return False

    return True


# ============================================================
# ENTRY FRESHNESS CHECK
# ============================================================

def entry_is_still_fresh(
    tf5,
    risk_data
):
    """
    Ensure the current price has not moved too far away
    from the calculated entry.

    This is important because a technically valid signal
    can become stale after a sudden price movement.
    """

    try:

        current_price = float(
            tf5["close"]
        )

        atr = float(
            tf5["atr"]
        )

        entry = float(
            risk_data["entry"]
        )

    except (
        KeyError,
        TypeError,
        ValueError
    ):

        return False

    if atr <= 0:

        return False

    # --------------------------------------------------------
    # Distance from entry
    # --------------------------------------------------------

    price_distance = abs(
        current_price - entry
    )

    max_allowed_distance = (
        atr * MAX_ENTRY_DRIFT_ATR
    )

    # --------------------------------------------------------
    # Fresh entry
    # --------------------------------------------------------

    return (
        price_distance
        <= max_allowed_distance
    )


# ============================================================
# VALIDATE RISK DATA
# ============================================================

def validate_risk_data(
    risk_data
):
    """
    Validate the output from risk_manager.py.
    """

    if not isinstance(
        risk_data,
        dict
    ):

        return False

    required_fields = [
        "entry",
        "stop_loss",
        "tp1",
        "tp2",
        "tp3",
        "risk_reward"
    ]

    for field in required_fields:

        if field not in risk_data:

            return False

        try:

            value = float(
                risk_data[field]
            )

        except (
            TypeError,
            ValueError
        ):

            return False

        if value <= 0:

            return False

    # --------------------------------------------------------
    # Risk / reward
    # --------------------------------------------------------

    try:

        risk_reward = float(
            risk_data["risk_reward"]
        )

    except (
        TypeError,
        ValueError
    ):

        return False

    if risk_reward <= 0:

        return False

    return True


# ============================================================
# SCAN ONE SYMBOL
# ============================================================

def scan_symbol(
    symbol
):
    """
    Scan one symbol through the complete trading pipeline.

    Pipeline:

        Binance
           ↓
        Multi-Timeframe
           ↓
        Indicators + SMC
           ↓
        Signal Engine
           ↓
        Market Quality
           ↓
        Risk Manager
           ↓
        Entry Freshness
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
            f"Skipped: incomplete timeframe data"
        )

        return None

    # ========================================================
    # SIGNAL GENERATION
    # ========================================================

    signal_data = generate_signal(
        mtf_data
    )

    if not validate_signal_data(
        signal_data
    ):

        return None

    # ========================================================
    # DEBUG LOG
    # ========================================================

    log_info(
        f"{symbol} | "
        f"Score={signal_data.get('score')} | "
        f"Direction={signal_data.get('direction')} | "
        f"Confidence={signal_data.get('confidence')} | "
        f"Signal={signal_data.get('signal')}"
    )

    # ========================================================
    # 5M DATA
    # ========================================================

    tf5 = mtf_data.get(
        "5m"
    )

    if not isinstance(
        tf5,
        dict
    ):

        return None

    # ========================================================
    # MARKET QUALITY
    # ========================================================

    if not valid_market_conditions(
        tf5
    ):

        log_info(
            f"{symbol} | "
            f"Skipped: insufficient market volatility"
        )

        return None

    # ========================================================
    # CURRENT PRICE + ATR
    # ========================================================

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

    if price <= 0:

        return None

    if atr <= 0:

        return None

    # ========================================================
    # RISK MANAGER
    # ========================================================

    risk_data = calculate_trade(
        price,
        atr,
        signal_data
    )

    if not validate_risk_data(
        risk_data
    ):

        log_info(
            f"{symbol} | "
            f"Skipped: invalid risk/TP calculation"
        )

        return None

    # ========================================================
    # ENTRY FRESHNESS
    # ========================================================

    if not entry_is_still_fresh(
        tf5,
        risk_data
    ):

        log_info(
            f"{symbol} | "
            f"Skipped: entry is too far from current setup"
        )

        return None

    # ========================================================
    # SIGNAL ID
    # ========================================================

    signal_id = create_signal_id(
        symbol,
        signal_data
    )

    # ========================================================
    # DUPLICATE PROTECTION
    # ========================================================

    if is_duplicate(
        signal_id
    ):

        log_info(
            f"{symbol} | "
            f"Skipped: duplicate signal"
        )

        return None

    # ========================================================
    # FORMAT SIGNAL
    # ========================================================

    message = format_signal(
        symbol,
        signal_data,
        risk_data
    )

    if not message:

        log_info(
            f"{symbol} | "
            f"Skipped: formatter returned empty message"
        )

        return None

    # ========================================================
    # REMEMBER SIGNAL
    # ========================================================

    remember_signal(
        signal_id
    )

    # ========================================================
    # RETURN
    # ========================================================

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

    Only signals that pass every validation layer
    are returned.
    """

    # --------------------------------------------------------
    # Clean old memory
    # --------------------------------------------------------

    cleanup_old_signals()

    # --------------------------------------------------------
    # Get watchlist
    # --------------------------------------------------------

    watchlist = get_watchlist()

    if not watchlist:

        log_info(
            "Watchlist is empty."
        )

        return []

    results = []

    log_info(
        f"Starting market scan: "
        f"{len(watchlist)} symbols"
    )

    # ========================================================
    # SCAN EACH SYMBOL
    # ========================================================

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

            log_info(
                f"{symbol} | "
                f"Valid signal generated"
            )

        except Exception:

            log_error(
                f"Error while scanning {symbol}\n"
                + traceback.format_exc()
            )

    # ========================================================
    # SCAN SUMMARY
    # ========================================================

    log_info(
        f"Scan completed | "
        f"New signals={len(results)}"
    )

    return results


# ============================================================
# AUTO SCAN
# ============================================================

def auto_scan():
    """
    Main automatic scanning entry point.

    main.py controls the scheduling interval.

    The scanner itself performs all signal validation.
    """

    try:

        return scan_market()

    except Exception:

        log_error(
            "Fatal error during auto scan\n"
            + traceback.format_exc()
        )

        return []