from binance_api import get_candles
from indicators import add_indicators
from smc import analyze_smc


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
# REQUIRED SMC FIELDS
# ============================================================

REQUIRED_SMC_FIELDS = [
    "structure",
    "bos",
    "choch",
    "liquidity_sweep",
    "swing_high",
    "previous_swing_high",
    "swing_low",
    "previous_swing_low",
    "fvg",
    "order_block"
]


# ============================================================
# VALIDATE NUMERIC VALUE
# ============================================================

def is_valid_number(value):
    """
    Check whether a value is a valid finite number.
    """

    try:

        value = float(value)

        return (
            value == value
            and value not in (
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
# VALIDATE SMC
# ============================================================

def validate_smc(smc_data):
    """
    Validate the complete SMC response.

    Some SMC values are legitimately None, such as BOS
    when no break has occurred. Therefore validation only
    requires the keys to exist.
    """

    if not isinstance(
        smc_data,
        dict
    ):

        return False

    for field in REQUIRED_SMC_FIELDS:

        if field not in smc_data:

            return False

    # --------------------------------------------------------
    # FVG structure
    # --------------------------------------------------------

    fvg = smc_data.get(
        "fvg"
    )

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
    # Order block structure
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

            return None

        # ====================================================
        # INDICATORS
        # ====================================================

        df = add_indicators(
            df
        )

        if df is None or df.empty:

            return None

        # ====================================================
        # INDICATOR VALIDATION
        # ====================================================

        for column in REQUIRED_INDICATORS:

            if column not in df.columns:

                return None

        # ----------------------------------------------------
        # Latest row
        # ----------------------------------------------------

        last = df.iloc[-1]

        # ----------------------------------------------------
        # Validate latest indicator values
        # ----------------------------------------------------

        for column in REQUIRED_INDICATORS:

            if not is_valid_number(
                last[column]
            ):

                return None

        # ====================================================
        # SMC
        # ====================================================

        smc_data = analyze_smc(
            df
        )

        if not validate_smc(
            smc_data
        ):

            return None

        # ====================================================
        # TIMEFRAME SNAPSHOT
        # ====================================================

        result = {}

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

    except Exception:

        return None


# ============================================================
# ANALYZE COMPLETE SYMBOL
# ============================================================

def analyze_symbol(symbol):
    """
    Analyze all required timeframes.

    Required:

        5m
        15m
        1h
        4h
        1d

    The symbol is rejected if any required timeframe fails.

    This prevents the Signal Engine from making a decision
    using incomplete market information.
    """

    result = {}

    for timeframe in TIMEFRAMES:

        data = analyze_timeframe(
            symbol,
            timeframe
        )

        if data is None:

            return None

        result[timeframe] = data

    # ========================================================
    # FINAL VALIDATION
    # ========================================================

    for timeframe in TIMEFRAMES:

        if timeframe not in result:

            return None

        if not isinstance(
            result[timeframe],
            dict
        ):

            return None

        if "smc" not in result[timeframe]:

            return None

    return result