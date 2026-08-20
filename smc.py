from typing import Dict, Optional


# ============================================================
# SMC CONFIGURATION
# ============================================================

SWING_LEFT = 3
SWING_RIGHT = 3

FVG_MIN_SIZE_ATR = 0.10

ORDER_BLOCK_LOOKBACK = 12

# Minimum candle-body / ATR ratio for displacement.
MIN_DISPLACEMENT_ATR = 0.50


# ============================================================
# EMPTY RESULTS
# ============================================================

def empty_fvg() -> Dict:
    return {
        "type": None,
        "upper": None,
        "lower": None,
        "size": None
    }


def empty_order_block() -> Dict:
    return {
        "type": None,
        "high": None,
        "low": None
    }


def empty_smc() -> Dict:
    return {
        "structure": "NEUTRAL",
        "bos": None,
        "choch": None,
        "liquidity_sweep": None,

        "swing_high": None,
        "previous_swing_high": None,

        "swing_low": None,
        "previous_swing_low": None,

        "fvg": empty_fvg(),
        "order_block": empty_order_block()
    }


# ============================================================
# DATA VALIDATION
# ============================================================

def has_required_columns(df) -> bool:

    if df is None:
        return False

    required_columns = {
        "open",
        "high",
        "low",
        "close"
    }

    try:
        return required_columns.issubset(
            df.columns
        )

    except Exception:
        return False


def safe_float(value) -> Optional[float]:

    try:

        number = float(value)

        if number != number:
            return None

        if number in (
            float("inf"),
            float("-inf")
        ):
            return None

        return number

    except (
        TypeError,
        ValueError
    ):

        return None


# ============================================================
# SWING DETECTION
# ============================================================

def find_swings(
    df,
    left: int = SWING_LEFT,
    right: int = SWING_RIGHT
):
    """
    Detect confirmed swing highs and swing lows.

    A swing requires candles on both sides of the candidate.
    Therefore the latest few candles cannot automatically
    become confirmed swings.
    """

    data = df.copy()

    data["swing_high"] = False
    data["swing_low"] = False

    if not has_required_columns(data):
        return data

    if left < 1 or right < 1:
        return data

    minimum_length = (
        left + right + 1
    )

    if len(data) < minimum_length:
        return data

    for i in range(
        left,
        len(data) - right
    ):

        current_high = safe_float(
            data["high"].iloc[i]
        )

        current_low = safe_float(
            data["low"].iloc[i]
        )

        if (
            current_high is None
            or current_low is None
        ):
            continue

        try:

            left_highs = (
                data["high"]
                .iloc[i - left:i]
                .astype(float)
            )

            right_highs = (
                data["high"]
                .iloc[i + 1:i + right + 1]
                .astype(float)
            )

            left_lows = (
                data["low"]
                .iloc[i - left:i]
                .astype(float)
            )

            right_lows = (
                data["low"]
                .iloc[i + 1:i + right + 1]
                .astype(float)
            )

        except (
            TypeError,
            ValueError
        ):

            continue

        # ----------------------------------------------------
        # Swing High
        # ----------------------------------------------------

        if (
            current_high > left_highs.max()
            and current_high > right_highs.max()
        ):

            data.at[
                data.index[i],
                "swing_high"
            ] = True

        # ----------------------------------------------------
        # Swing Low
        # ----------------------------------------------------

        if (
            current_low < left_lows.min()
            and current_low < right_lows.min()
        ):

            data.at[
                data.index[i],
                "swing_low"
            ] = True

    return data


# ============================================================
# STRUCTURE LEVELS
# ============================================================

def get_structure_levels(df) -> Dict:

    if not has_required_columns(df):

        return {
            "swing_high": None,
            "previous_swing_high": None,
            "swing_low": None,
            "previous_swing_low": None
        }

    data = find_swings(df)

    swing_highs = data[
        data["swing_high"]
    ]

    swing_lows = data[
        data["swing_low"]
    ]

    latest_swing_high = None
    previous_swing_high = None

    latest_swing_low = None
    previous_swing_low = None

    if len(swing_highs) >= 1:

        latest_swing_high = safe_float(
            swing_highs["high"].iloc[-1]
        )

    if len(swing_highs) >= 2:

        previous_swing_high = safe_float(
            swing_highs["high"].iloc[-2]
        )

    if len(swing_lows) >= 1:

        latest_swing_low = safe_float(
            swing_lows["low"].iloc[-1]
        )

    if len(swing_lows) >= 2:

        previous_swing_low = safe_float(
            swing_lows["low"].iloc[-2]
        )

    return {
        "swing_high": latest_swing_high,
        "previous_swing_high": previous_swing_high,
        "swing_low": latest_swing_low,
        "previous_swing_low": previous_swing_low
    }


# ============================================================
# MARKET STRUCTURE
# ============================================================

def detect_structure(df) -> Dict:
    """
    Determine:

        BULLISH:
            Higher High + Higher Low

        BEARISH:
            Lower High + Lower Low

        NEUTRAL:
            Anything else

    BOS:
        Latest closed candle closes beyond the latest
        confirmed swing level.

    CHOCH:
        A break against the previously established structure.
    """

    if not has_required_columns(df):

        return {
            "structure": "NEUTRAL",
            "bos": None,
            "choch": None,
            **get_structure_levels(df)
        }

    data = find_swings(df)

    swing_highs = data[
        data["swing_high"]
    ]

    swing_lows = data[
        data["swing_low"]
    ]

    levels = get_structure_levels(
        df
    )

    if (
        len(swing_highs) < 2
        or len(swing_lows) < 2
    ):

        return {
            "structure": "NEUTRAL",
            "bos": None,
            "choch": None,
            **levels
        }

    latest_high = safe_float(
        swing_highs["high"].iloc[-1]
    )

    previous_high = safe_float(
        swing_highs["high"].iloc[-2]
    )

    latest_low = safe_float(
        swing_lows["low"].iloc[-1]
    )

    previous_low = safe_float(
        swing_lows["low"].iloc[-2]
    )

    last_close = safe_float(
        data["close"].iloc[-1]
    )

    if any(
        value is None
        for value in [
            latest_high,
            previous_high,
            latest_low,
            previous_low,
            last_close
        ]
    ):

        return {
            "structure": "NEUTRAL",
            "bos": None,
            "choch": None,
            **levels
        }

    # ========================================================
    # ESTABLISHED STRUCTURE
    # ========================================================

    bullish_structure = (
        latest_high > previous_high
        and latest_low > previous_low
    )

    bearish_structure = (
        latest_high < previous_high
        and latest_low < previous_low
    )

    if bullish_structure:

        structure = "BULLISH"

    elif bearish_structure:

        structure = "BEARISH"

    else:

        structure = "NEUTRAL"

    # ========================================================
    # BREAK DETECTION
    # ========================================================

    bos = None
    choch = None

    bullish_break = (
        last_close > latest_high
    )

    bearish_break = (
        last_close < latest_low
    )

    if bullish_break:

        if structure == "BEARISH":

            choch = "BULLISH"

        else:

            bos = "BULLISH"

    elif bearish_break:

        if structure == "BULLISH":

            choch = "BEARISH"

        else:

            bos = "BEARISH"

    return {
        "structure": structure,
        "bos": bos,
        "choch": choch,
        **levels
    }


# ============================================================
# LIQUIDITY SWEEP
# ============================================================

def detect_liquidity_sweep(df):

    """
    Detect sweep/rejection of the latest confirmed
    swing liquidity level.

    Bearish:
        High takes previous swing high
        AND close returns below it.

    Bullish:
        Low takes previous swing low
        AND close returns above it.
    """

    if not has_required_columns(df):
        return None

    data = find_swings(df)

    if len(data) < 3:
        return None

    last = data.iloc[-1]

    last_high = safe_float(
        last["high"]
    )

    last_low = safe_float(
        last["low"]
    )

    last_close = safe_float(
        last["close"]
    )

    if any(
        value is None
        for value in [
            last_high,
            last_low,
            last_close
        ]
    ):

        return None

    swing_highs = data[
        data["swing_high"]
    ]

    swing_lows = data[
        data["swing_low"]
    ]

    # ========================================================
    # BEARISH SWEEP
    # ========================================================

    if not swing_highs.empty:

        valid_highs = swing_highs[
            swing_highs.index
            != data.index[-1]
        ]

        if not valid_highs.empty:

            level = safe_float(
                valid_highs[
                    "high"
                ].iloc[-1]
            )

            if (
                level is not None
                and last_high > level
                and last_close < level
            ):

                return "BEARISH"

    # ========================================================
    # BULLISH SWEEP
    # ========================================================

    if not swing_lows.empty:

        valid_lows = swing_lows[
            swing_lows.index
            != data.index[-1]
        ]

        if not valid_lows.empty:

            level = safe_float(
                valid_lows[
                    "low"
                ].iloc[-1]
            )

            if (
                level is not None
                and last_low < level
                and last_close > level
            ):

                return "BULLISH"

    return None


# ============================================================
# FAIR VALUE GAP
# ============================================================

def detect_fvg(df) -> Dict:

    empty = empty_fvg()

    if df is None:
        return empty

    if len(df) < 3:
        return empty

    if not has_required_columns(df):
        return empty

    data = df.reset_index(
        drop=True
    )

    candle_1 = data.iloc[-3]
    candle_2 = data.iloc[-2]
    candle_3 = data.iloc[-1]

    candle_1_high = safe_float(
        candle_1["high"]
    )

    candle_1_low = safe_float(
        candle_1["low"]
    )

    candle_2_open = safe_float(
        candle_2["open"]
    )

    candle_2_close = safe_float(
        candle_2["close"]
    )

    candle_3_high = safe_float(
        candle_3["high"]
    )

    candle_3_low = safe_float(
        candle_3["low"]
    )

    if any(
        value is None
        for value in [
            candle_1_high,
            candle_1_low,
            candle_2_open,
            candle_2_close,
            candle_3_high,
            candle_3_low
        ]
    ):

        return empty

    atr = None

    if "atr" in data.columns:

        atr = safe_float(
            data["atr"].iloc[-1]
        )

        if atr is not None and atr <= 0:
            atr = None

    # ========================================================
    # BULLISH FVG
    # ========================================================

    bullish_gap = (
        candle_1_high < candle_3_low
    )

    bullish_displacement = (
        candle_2_close > candle_2_open
    )

    if (
        bullish_gap
        and bullish_displacement
    ):

        lower = candle_1_high
        upper = candle_3_low
        size = upper - lower

        if (
            atr is None
            or size >= atr * FVG_MIN_SIZE_ATR
        ):

            return {
                "type": "BULLISH",
                "upper": upper,
                "lower": lower,
                "size": size
            }

    # ========================================================
    # BEARISH FVG
    # ========================================================

    bearish_gap = (
        candle_1_low > candle_3_high
    )

    bearish_displacement = (
        candle_2_close < candle_2_open
    )

    if (
        bearish_gap
        and bearish_displacement
    ):

        upper = candle_1_low
        lower = candle_3_high
        size = upper - lower

        if (
            atr is None
            or size >= atr * FVG_MIN_SIZE_ATR
        ):

            return {
                "type": "BEARISH",
                "upper": upper,
                "lower": lower,
                "size": size
            }

    return empty


# ============================================================
# ORDER BLOCK
# ============================================================

def detect_order_block(df) -> Dict:

    """
    Detect a recent opposite candle that precedes
    meaningful displacement.

    This deliberately avoids treating every opposite-color
    candle as an Order Block.
    """

    empty = empty_order_block()

    if df is None:
        return empty

    if len(df) < 5:
        return empty

    if not has_required_columns(df):
        return empty

    data = df.reset_index(
        drop=True
    )

    last = data.iloc[-1]

    last_open = safe_float(
        last["open"]
    )

    last_close = safe_float(
        last["close"]
    )

    last_high = safe_float(
        last["high"]
    )

    last_low = safe_float(
        last["low"]
    )

    if any(
        value is None
        for value in [
            last_open,
            last_close,
            last_high,
            last_low
        ]
    ):

        return empty

    body_size = abs(
        last_close - last_open
    )

    # ========================================================
    # DISPLACEMENT FILTER
    # ========================================================

    displacement_valid = True

    if "atr" in data.columns:

        atr = safe_float(
            data["atr"].iloc[-1]
        )

        if (
            atr is not None
            and atr > 0
        ):

            displacement_valid = (
                body_size
                >= atr * MIN_DISPLACEMENT_ATR
            )

    if not displacement_valid:
        return empty

    # ========================================================
    # SEARCH RECENT OPPOSITE CANDLE
    # ========================================================

    recent_start = max(
        0,
        len(data)
        - ORDER_BLOCK_LOOKBACK
        - 1
    )

    recent = data.iloc[
        recent_start:-1
    ]

    if recent.empty:
        return empty

    # ========================================================
    # BULLISH ORDER BLOCK
    # ========================================================

    if last_close > last_open:

        candidates = recent[
            recent["close"]
            < recent["open"]
        ]

        if not candidates.empty:

            candle = candidates.iloc[-1]

            high = safe_float(
                candle["high"]
            )

            low = safe_float(
                candle["low"]
            )

            if (
                high is not None
                and low is not None
            ):

                return {
                    "type": "BULLISH",
                    "high": high,
                    "low": low
                }

    # ========================================================
    # BEARISH ORDER BLOCK
    # ========================================================

    if last_close < last_open:

        candidates = recent[
            recent["close"]
            > recent["open"]
        ]

        if not candidates.empty:

            candle = candidates.iloc[-1]

            high = safe_float(
                candle["high"]
            )

            low = safe_float(
                candle["low"]
            )

            if (
                high is not None
                and low is not None
            ):

                return {
                    "type": "BEARISH",
                    "high": high,
                    "low": low
                }

    return empty


# ============================================================
# COMPLETE SMC ANALYSIS
# ============================================================

def analyze_smc(df) -> Dict:
    """
    Run the complete SMC engine.

    Output remains compatible with signals.py:

        structure
        bos
        choch
        liquidity_sweep
        swing_high
        previous_swing_high
        swing_low
        previous_swing_low
        fvg
        order_block
    """

    if df is None:
        return empty_smc()

    if getattr(df, "empty", True):
        return empty_smc()

    if not has_required_columns(df):
        return empty_smc()

    try:

        structure = detect_structure(
            df
        )

        liquidity_sweep = (
            detect_liquidity_sweep(df)
        )

        fvg = detect_fvg(
            df
        )

        order_block = detect_order_block(
            df
        )

        return {
            "structure": structure.get(
                "structure",
                "NEUTRAL"
            ),

            "bos": structure.get(
                "bos"
            ),

            "choch": structure.get(
                "choch"
            ),

            "liquidity_sweep":
                liquidity_sweep,

            "swing_high": structure.get(
                "swing_high"
            ),

            "previous_swing_high":
                structure.get(
                    "previous_swing_high"
                ),

            "swing_low": structure.get(
                "swing_low"
            ),

            "previous_swing_low":
                structure.get(
                    "previous_swing_low"
                ),

            "fvg": fvg,

            "order_block":
                order_block
        }

    except Exception:

        return empty_smc()