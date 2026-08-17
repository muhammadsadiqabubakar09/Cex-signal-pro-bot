from binance_api import get_candles
from indicators import add_indicators
from smc import analyze_smc
from logger import log_info, log_warning, log_error


# ============================================================
# TIMEFRAME CONFIGURATION
# ============================================================

# These timeframes MUST be available
REQUIRED_TIMEFRAMES = [
    "5m",
    "15m",
    "1h",
    "4h"
]

# Daily timeframe is useful for higher-timeframe confirmation,
# but it is NOT mandatory.
OPTIONAL_TIMEFRAMES = [
    "1d"
]

ALL_TIMEFRAMES = (
    REQUIRED_TIMEFRAMES
    + OPTIONAL_TIMEFRAMES
)

CANDLE_LIMIT = 250


# ============================================================
# REQUIRED INDICATORS
# ============================================================

REQUIRED_INDICATORS = [
    "ema20",
    "ema50",
    "ema200",

    "rsi",

    "stoch_rsi",
    "stoch_rsi_k",
    "stoch_rsi_d",

    "macd",
    "macd_signal",
    "macd_hist",

    "adx",

    "atr",

    "bb_upper",
    "bb_middle",
    "bb_lower",
    "bb_width",

    "vwap",

    "volume",
    "volume_sma"
]


# ============================================================
# REQUIRED PRICE FIELDS
# ============================================================

REQUIRED_PRICE_FIELDS = [
    "open",
    "high",
    "low",
    "close",
    "volume"
]


# ============================================================
# REQUIRED SMC FIELDS
# ============================================================

REQUIRED_SMC_FIELDS = [
    "structure",
    "bos",
    "choch",
    "liquidity_sweep",
    "fvg",
    "order_block"
]


# ============================================================
# NUMBER VALIDATION
# ============================================================

def is_valid_number(value):
    """
    Check whether a value is a valid finite number.
    """

    try:

        number = float(value)

        return (
            number == number
            and number not in (
                float("inf"),
                float("-inf")
            )
        )

    except (
        TypeError,
        ValueError
    ):

        return False


# ============================================================
# SMC VALIDATION
# ============================================================

def validate_smc(smc_data):
    """
    Validate the SMC structure produced by smc.py.
    """

    if not isinstance(
        smc_data,
        dict
    ):
        return False

    # --------------------------------------------------------
    # Main SMC fields
    # --------------------------------------------------------

    for field in REQUIRED_SMC_FIELDS:

        if field not in smc_data:

            return False

    # --------------------------------------------------------
    # FVG
    # --------------------------------------------------------

    fvg = smc_data.get("fvg")

    if not isinstance(
        fvg,
        dict
    ):
        return False

    for field in [
        "type",
        "upper",
        "lower",
        "size"
    ]:

        if field not in fvg:

            return False

    # --------------------------------------------------------
    # Order Block
    # --------------------------------------------------------

    order_block = smc_data.get(
        "order_block"
    )

    if not isinstance(
        order_block,
        dict
    ):
        return False

    for field in [
        "type",
        "high",
        "low"
    ]:

        if field not in order_block:

            return False

    return True


# ============================================================
# ANALYZE ONE TIMEFRAME
# ============================================================

def analyze_timeframe(
    symbol,
    interval
):
    """
    Analyze one timeframe.

    Pipeline:

        Binance
           ↓
        OHLCV
           ↓
        Indicators
           ↓
        SMC
           ↓
        Validation
           ↓
        Timeframe Snapshot
    """

    try:

        # ====================================================
        # MARKET DATA
        # ====================================================

        df = get_candles(
            symbol,
            interval,
            CANDLE_LIMIT
        )

        if df is None or df.empty:

            log_warning(
                f"{symbol} | {interval} | "
                f"FAILED: no market data"
            )

            return None

        # ====================================================
        # PRICE DATA VALIDATION
        # ====================================================

        for column in REQUIRED_PRICE_FIELDS:

            if column not in df.columns:

                log_warning(
                    f"{symbol} | {interval} | "
                    f"FAILED: missing price field "
                    f"{column}"
                )

                return None

        # ====================================================
        # TECHNICAL INDICATORS
        # ====================================================

        df = add_indicators(
            df
        )

        if df is None or df.empty:

            log_warning(
                f"{symbol} | {interval} | "
                f"FAILED: indicators returned empty data"
            )

            return None

        # ====================================================
        # INDICATOR VALIDATION
        # ====================================================

        for column in REQUIRED_INDICATORS:

            if column not in df.columns:

                log_warning(
                    f"{symbol} | {interval} | "
                    f"FAILED: missing indicator "
                    f"{column}"
                )

                return None

        # ====================================================
        # LATEST CANDLE
        # ====================================================

        last = df.iloc[-1]

        # ====================================================
        # PRICE VALIDATION
        # ====================================================

        for column in REQUIRED_PRICE_FIELDS:

            if not is_valid_number(
                last[column]
            ):

                log_warning(
                    f"{symbol} | {interval} | "
                    f"FAILED: invalid price "
                    f"{column}"
                )

                return None

        # ====================================================
        # INDICATOR VALUE VALIDATION
        # ====================================================

        for column in REQUIRED_INDICATORS:

            if not is_valid_number(
                last[column]
            ):

                log_warning(
                    f"{symbol} | {interval} | "
                    f"FAILED: invalid indicator "
                    f"{column}"
                )

                return None

        # ====================================================
        # SMC ANALYSIS
        # ====================================================

        smc_data = analyze_smc(
            df
        )

        if not validate_smc(
            smc_data
        ):

            log_warning(
                f"{symbol} | {interval} | "
                f"FAILED: invalid SMC structure"
            )

            return None

        # ====================================================
        # BUILD SNAPSHOT
        # ====================================================

        result = {}

        # ----------------------------------------------------
        # Price data
        # ----------------------------------------------------

        for column in REQUIRED_PRICE_FIELDS:

            result[column] = float(
                last[column]
            )

        # ----------------------------------------------------
        # Indicators
        # ----------------------------------------------------

        for column in REQUIRED_INDICATORS:

            result[column] = float(
                last[column]
            )

        # ----------------------------------------------------
        # SMC
        # ----------------------------------------------------

        result["smc"] = smc_data

        # ----------------------------------------------------
        # Metadata
        # ----------------------------------------------------

        result["timeframe"] = interval

        result["symbol"] = str(
            symbol
        ).upper()

        return result

    except Exception as error:

        log_error(
            f"{symbol} | {interval} | "
            f"ANALYSIS ERROR: {error}"
        )

        return None


# ============================================================
# ANALYZE COMPLETE SYMBOL
# ============================================================

def analyze_symbol(symbol):
    """
    Analyze the complete multi-timeframe structure.

    Mandatory:
        5m
        15m
        1h
        4h

    Optional:
        1d

    The symbol is rejected ONLY when a mandatory timeframe
    fails.

    If 1d fails because of insufficient history, Binance
    restrictions, or a temporary API problem, the symbol
    remains valid.
    """

    symbol = str(
        symbol
    ).upper().strip()

    if not symbol:

        return None

    result = {}

    log_info(
        f"{symbol} | "
        f"Starting multi-timeframe analysis"
    )

    # ========================================================
    # REQUIRED TIMEFRAMES
    # ========================================================

    for timeframe in REQUIRED_TIMEFRAMES:

        data = analyze_timeframe(
            symbol,
            timeframe
        )

        if data is None:

            log_warning(
                f"{symbol} | "
                f"MTF FAILED | "
                f"Required timeframe: {timeframe}"
            )

            return None

        result[timeframe] = data

        log_info(
            f"{symbol} | "
            f"{timeframe}: OK"
        )

    # ========================================================
    # OPTIONAL 1D TIMEFRAME
    # ========================================================

    for timeframe in OPTIONAL_TIMEFRAMES:

        data = analyze_timeframe(
            symbol,
            timeframe
        )

        if data is None:

            # ------------------------------------------------
            # 1D failure does NOT reject the symbol
            # ------------------------------------------------

            result[timeframe] = None

            log_warning(
                f"{symbol} | "
                f"{timeframe}: unavailable "
                f"(optional timeframe)"
            )

            continue

        result[timeframe] = data

        log_info(
            f"{symbol} | "
            f"{timeframe}: OK"
        )

    # ========================================================
    # FINAL VALIDATION
    # ========================================================

    # --------------------------------------------------------
    # Required timeframes must exist
    # --------------------------------------------------------

    for timeframe in REQUIRED_TIMEFRAMES:

        if timeframe not in result:

            log_warning(
                f"{symbol} | "
                f"MTF FAILED | "
                f"Missing required timeframe: {timeframe}"
            )

            return None

        timeframe_data = result[
            timeframe
        ]

        if not isinstance(
            timeframe_data,
            dict
        ):

            log_warning(
                f"{symbol} | "
                f"MTF FAILED | "
                f"Invalid {timeframe} data"
            )

            return None

        # ----------------------------------------------------
        # Close validation
        # ----------------------------------------------------

        if not is_valid_number(
            timeframe_data.get("close")
        ):

            log_warning(
                f"{symbol} | "
                f"MTF FAILED | "
                f"Invalid {timeframe} close"
            )

            return None

        # ----------------------------------------------------
        # ATR validation
        # ----------------------------------------------------

        if not is_valid_number(
            timeframe_data.get("atr")
        ):

            log_warning(
                f"{symbol} | "
                f"MTF FAILED | "
                f"Invalid {timeframe} ATR"
            )

            return None

        # ----------------------------------------------------
        # SMC validation
        # ----------------------------------------------------

        if not validate_smc(
            timeframe_data.get("smc")
        ):

            log_warning(
                f"{symbol} | "
                f"MTF FAILED | "
                f"Invalid {timeframe} SMC"
            )

            return None

    # ========================================================
    # FINAL RESULT
    # ========================================================

    if result.get("1d") is None:

        log_info(
            f"{symbol} | "
            f"MTF COMPLETE | "
            f"5m + 15m + 1h + 4h validated | "
            f"1d unavailable"
        )

    else:

        log_info(
            f"{symbol} | "
            f"MTF COMPLETE | "
            f"5m + 15m + 1h + 4h + 1d validated"
        )

    return result