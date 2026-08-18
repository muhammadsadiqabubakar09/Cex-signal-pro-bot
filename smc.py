from typing import Dict, Optional


# ============================================================
# SMC CONFIGURATION
# ============================================================

SWING_LEFT = 3
SWING_RIGHT = 3

FVG_MIN_SIZE_ATR = 0.10

# Number of recent candles inspected for an order block.
ORDER_BLOCK_LOOKBACK = 8


# ============================================================
# EMPTY RESULTS
# ============================================================

def empty_fvg() -> Dict:
    """
    Return a safe empty Fair Value Gap structure.
    """

    return {
        "type": None,
        "upper": None,
        "lower": None,
        "size": None
    }


def empty_order_block() -> Dict:
    """
    Return a safe empty Order Block structure.
    """

    return {
        "type": None,
        "high": None,
        "low": None
    }


def empty_smc() -> Dict:
    """
    Return a safe empty SMC result.

    Field names are kept compatible with signals.py,
    multi_timeframe.py and risk_manager.py.
    """

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
    """
    Check that the DataFrame contains the OHLC columns
    required by the SMC engine.
    """

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

    A swing is confirmed only when candles exist on both
    sides of the candidate candle.

    The current unfinished candle is not specially used here;
    binance_api.py already provides CLOSED candles only.
    """

    data = df.copy()

    data["swing_high"] = False
    data["swing_low"] = False

    if not has_required_columns(data):
        return data

    if left < 1 or right < 1:
        return data

    minimum_length = left + right + 1

    if len(data) < minimum_length:
        return data

    for i in range(
        left,
        len(data) - right
    ):

        try:

            current_high = float(
                data["high"].iloc[i]
            )

            current_low = float(
                data["low"].iloc[i]
            )

            left_highs = data[
                "high"
            ].iloc[
                i - left:i
            ].astype(float)

            right_highs = data[
                "high"
            ].iloc[
                i + 1:i + right + 1
            ].astype(float)

            left_lows = data[
                "low"
            ].iloc[
                i - left:i
            ].astype(float)

            right_lows = data[
                "low"
            ].iloc[
                i + 1:i + right + 1
            ].astype(float)

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
    """
    Return the latest two confirmed swing highs and lows.
    """

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

    latest_swing_high: Optional[float] = None
    previous_swing_high: Optional[float] = None

    latest_swing_low: Optional[float] = None
    previous_swing_low: Optional[float] = None

    if len(swing_highs) >= 1:

        latest_swing_high = float(
            swing_highs["high"].iloc[-1]
        )

    if len(swing_highs) >= 2:

        previous_swing_high = float(
            swing_highs["high"].iloc[-2]
        )

    if len(swing_lows) >= 1:

        latest_swing_low = float(
            swing_lows["low"].iloc[-1]
        )

    if len(swing_lows) >= 2:

        previous_swing_low = float(
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
    Detect market structure using confirmed swing points.

    Structure:

        Higher High + Higher Low = BULLISH
        Lower High + Lower Low   = BEARISH
        Otherwise                = NEUTRAL

    BOS is detected when the latest CLOSED candle breaks
    beyond the latest confirmed swing level.

    CHOCH is reported when that break is opposite the
    previously established structure.
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

    levels = get_structure_levels(df)

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

    try:

        latest_high = float(
            swing_highs["high"].iloc[-1]
        )

        previous_high = float(
            swing_highs["high"].iloc[-2]
        )

        latest_low = float(
            swing_lows["low"].iloc[-1]
        )

        previous_low = float(
            swing_lows["low"].iloc[-2]
        )

        last_close = float(
            data["close"].iloc[-1]
        )

    except (
        TypeError,
        ValueError
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
    # BREAK OF STRUCTURE
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

        bos = "BULLISH"

        if bearish_structure:
            choch = "BULLISH"

    elif bearish_break:

        bos = "BEARISH"

        if bullish_structure:
            choch = "BEARISH"

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
    Detect a liquidity sweep on the latest CLOSED candle.

    Bearish sweep:

        Current high trades above a previous confirmed
        swing high but closes back below that level.

    Bullish sweep:

        Current low trades below a previous confirmed
        swing low but closes back above that level.

    The latest swing itself is excluded when it is the
    current candle, preventing self-referencing.
    """

    if not has_required_columns(df):
        return None

    data = find_swings(df)

    if len(data) < 2:
        return None

    swing_highs = data[
        data["swing_high"]
    ]

    swing_lows = data[
        data["swing_low"]
    ]

    if (
        swing_highs.empty
        and swing_lows.empty
    ):
        return None

    try:

        last = data.iloc[-1]

        last_high = float(
            last["high"]
        )

        last_low = float(
            last["low"]
        )

        last_close = float(
            last["close"]
        )

    except (
        TypeError,
        ValueError
    ):

        return None

    # ========================================================
    # BEARISH LIQUIDITY SWEEP
    # ========================================================

    if not swing_highs.empty:

        valid_highs = swing_highs[
            swing_highs.index
            != data.index[-1]
        ]

        if not valid_highs.empty:

            level = float(
                valid_highs[
                    "high"
                ].iloc[-1]
            )

            if (
                last_high > level
                and last_close < level
            ):

                return "BEARISH"

    # ========================================================
    # BULLISH LIQUIDITY SWEEP
    # ========================================================

    if not swing_lows.empty:

        valid_lows = swing_lows[
            swing_lows.index
            != data.index[-1]
        ]

        if not valid_lows.empty:

            level = float(
                valid_lows[
                    "low"
                ].iloc[-1]
            )

            if (
                last_low < level
                and last_close > level
            ):

                return "BULLISH"

    return None


# ============================================================
# FAIR VALUE GAP
# ============================================================

def detect_fvg(df) -> Dict:
    """
    Detect the latest three-candle Fair Value Gap.

    Bullish FVG:

        Candle 1 high < Candle 3 low

    Bearish FVG:

        Candle 1 low > Candle 3 high

    The gap must satisfy the configured ATR minimum.
    """

    empty = empty_fvg()

    if df is None or len(df) < 3:
        return empty

    if not has_required_columns(df):
        return empty

    data = df.reset_index(
        drop=True
    )

    candle_1 = data.iloc[-3]
    candle_3 = data.iloc[-1]

    try:

        candle_1_high = float(
            candle_1["high"]
        )

        candle_1_low = float(
            candle_1["low"]
        )

        candle_3_high = float(
            candle_3["high"]
        )

        candle_3_low = float(
            candle_3["low"]
        )

    except (
        TypeError,
        ValueError
    ):

        return empty

    atr = None

    if "atr" in data.columns:

        try:

            atr_value = float(
                data["atr"].iloc[-1]
            )

            if atr_value > 0:
                atr = atr_value

        except (
            TypeError,
            ValueError
        ):

            atr = None

    # ========================================================
    # BULLISH FVG
    # ========================================================

    if candle_1_high < candle_3_low:

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

    if candle_1_low > candle_3_high:

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
    Detect a recent Order Block candidate.

    Bullish Order Block:

        The latest bullish displacement candle is preceded
        by a recent bearish candle.

    Bearish Order Block:

        The latest bearish displacement candle is preceded
        by a recent bullish candle.

    This remains a candidate detector rather than claiming
    that every opposite-color candle is a perfect institutional
    order block.
    """

    empty = empty_order_block()

    if df is None or len(df) < 5:
        return empty

    if not has_required_columns(df):
        return empty

    data = df.reset_index(
        drop=True
    )

    recent_start = max(
        0,
        len(data) - ORDER_BLOCK_LOOKBACK - 1
    )

    recent = data.iloc[
        recent_start:-1
    ]

    if recent.empty:
        return empty

    try:

        last = data.iloc[-1]

        last_open = float(
            last["open"]
        )

        last_close = float(
            last["close"]
        )

    except (
        TypeError,
        ValueError
    ):

        return empty

    # ========================================================
    # BULLISH ORDER BLOCK
    # ========================================================

    if last_close > last_open:

        bearish_candidates = recent[
            recent["close"]
            < recent["open"]
        ]

        if not bearish_candidates.empty:

            candle = bearish_candidates.iloc[-1]

            try:

                return {
                    "type": "BULLISH",

                    "high": float(
                        candle["high"]
                    ),

                    "low": float(
                        candle["low"]
                    )
                }

            except (
                TypeError,
                ValueError
            ):

                return empty

    # ========================================================
    # BEARISH ORDER BLOCK
    # ========================================================

    if last_close < last_open:

        bullish_candidates = recent[
            recent["close"]
            > recent["open"]
        ]

        if not bullish_candidates.empty:

            candle = bullish_candidates.iloc[-1]

            try:

                return {
                    "type": "BEARISH",

                    "high": float(
                        candle["high"]
                    ),

                    "low": float(
                        candle["low"]
                    )
                }

            except (
                TypeError,
                ValueError
            ):

                return empty

    return empty


# ============================================================
# COMPLETE SMC ANALYSIS
# ============================================================

def analyze_smc(df) -> Dict:
    """
    Run the complete SMC engine.

    Output:

        structure
        BOS
        CHOCH
        liquidity sweep
        swing levels
        FVG
        Order Block

    Any unexpected failure returns a safe empty result so
    one bad timeframe cannot crash the entire scanner.
    """

    if df is None or getattr(df, "empty", True):
        return empty_smc()

    if not has_required_columns(df):
        return empty_smc()

    try:

        structure = detect_structure(
            df
        )

        liquidity_sweep = detect_liquidity_sweep(
            df
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

            "previous_swing_high": structure.get(
                "previous_swing_high"
            ),

            "swing_low": structure.get(
                "swing_low"
            ),

            "previous_swing_low": structure.get(
                "previous_swing_low"
            ),

            "fvg": fvg,

            "order_block": order_block
        }

    except Exception:

        return empty_smc()