from binance_api import get_candles
from indicators import add_indicators
from smc import analyze_smc
from logger import log_info, log_warning, log_error


# ============================================================
# TIMEFRAME CONFIGURATION
# ============================================================

TIMEFRAMES = [
    "5m",
    "15m",
    "1h",
    "4h",
    "1d"
]

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

    try:
        value = float(value)

        return (
            value == value
            and value != float("inf")
            and value != float("-inf")
        )

    except (TypeError, ValueError):

        return False


# ============================================================
# SMC VALIDATION
# ============================================================

def validate_smc(smc_data):

    if not isinstance(smc_data, dict):

        return False

    # --------------------------------------------------------
    # Main fields
    # --------------------------------------------------------

    for field in REQUIRED_SMC_FIELDS:

        if field not in smc_data:

            return False

    # --------------------------------------------------------
    # FVG
    # --------------------------------------------------------

    fvg = smc_data.get("fvg")

    if not isinstance(fvg, dict):

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

    order_block = smc_data.get("order_block")

    if not isinstance(order_block, dict):

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

def analyze_timeframe(symbol, interval):

    try:

        log_info(
            f"{symbol} | {interval} | Starting analysis"
        )

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
                f"FAILED: no candle data"
            )

            return None

        if len(df) < 200:

            log_warning(
                f"{symbol} | {interval} | "
                f"FAILED: insufficient candles "
                f"({len(df)})"
            )

            return None

        # ====================================================
        # PRICE VALIDATION
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
        # INDICATORS
        # ====================================================

        df = add_indicators(df)

        if df is None or df.empty:

            log_warning(
                f"{symbol} | {interval} | "
                f"FAILED: indicators returned empty"
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
        # LATEST PRICE VALIDATION
        # ====================================================

        for column in REQUIRED_PRICE_FIELDS:

            if not is_valid_number(last[column]):

                log_warning(
                    f"{symbol} | {interval} | "
                    f"FAILED: invalid price "
                    f"{column}={last[column]}"
                )

                return None

        # ====================================================
        # LATEST INDICATOR VALIDATION
        # ====================================================

        for column in REQUIRED_INDICATORS:

            if not is_valid_number(last[column]):

                log_warning(
                    f"{symbol} | {interval} | "
                    f"FAILED: invalid indicator "
                    f"{column}={last[column]}"
                )

                return None

        # ====================================================
        # SMC
        # ====================================================

        smc_data = analyze_smc(df)

        if not validate_smc(smc_data):

            log_warning(
                f"{symbol} | {interval} | "
                f"FAILED: invalid SMC output"
            )

            return None

        # ====================================================
        # BUILD SNAPSHOT
        # ====================================================

        result = {}

        for column in REQUIRED_PRICE_FIELDS:

            result[column] = float(last[column])

        for column in REQUIRED_INDICATORS:

            result[column] = float(last[column])

        result["smc"] = smc_data
        result["timeframe"] = interval
        result["symbol"] = str(symbol).upper()

        log_info(
            f"{symbol} | {interval} | OK"
        )

        return result

    except Exception as error:

        log_error(
            f"{symbol} | {interval} | "
            f"ANALYSIS ERROR: {type(error).__name__}: {error}"
        )

        return None


# ============================================================
# ANALYZE COMPLETE SYMBOL
# ============================================================

def analyze_symbol(symbol):

    symbol = str(symbol).upper().strip()

    result = {}

    log_info(
        f"{symbol} | MTF analysis started"
    )

    # ========================================================
    # ANALYZE ALL TIMEFRAMES
    # ========================================================

    for timeframe in TIMEFRAMES:

        data = analyze_timeframe(
            symbol,
            timeframe
        )

        if data is None:

            log_warning(
                f"{symbol} | MTF FAILED | "
                f"Failed timeframe: {timeframe}"
            )

            return None

        result[timeframe] = data

    # ========================================================
    # FINAL VALIDATION
    # ========================================================

    missing = [
        tf for tf in TIMEFRAMES
        if tf not in result
    ]

    if missing:

        log_warning(
            f"{symbol} | MTF FAILED | "
            f"Missing: {missing}"
        )

        return None

    # ========================================================
    # FINAL DATA VALIDATION
    # ========================================================

    for timeframe in TIMEFRAMES:

        data = result[timeframe]

        if not isinstance(data, dict):

            log_warning(
                f"{symbol} | MTF FAILED | "
                f"{timeframe}: invalid snapshot"
            )

            return None

        if not is_valid_number(data.get("close")):

            log_warning(
                f"{symbol} | MTF FAILED | "
                f"{timeframe}: invalid close"
            )

            return None

        if not is_valid_number(data.get("atr")):

            log_warning(
                f"{symbol} | MTF FAILED | "
                f"{timeframe}: invalid ATR"
            )

            return None

        if not validate_smc(data.get("smc")):

            log_warning(
                f"{symbol} | MTF FAILED | "
                f"{timeframe}: invalid SMC"
            )

            return None

    # ========================================================
    # SUCCESS
    # ========================================================

    log_info(
        f"{symbol} | MTF COMPLETE | "
        f"5m + 15m + 1h + 4h + 1d validated"
    )

    return result