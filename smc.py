import pandas as pd


# ============================================================
# SMC CONFIGURATION
# ============================================================

SWING_LEFT = 3
SWING_RIGHT = 3

FVG_MIN_SIZE_ATR = 0.10


# ============================================================
# SWING DETECTION
# ============================================================

def find_swings(df, left=SWING_LEFT, right=SWING_RIGHT):
    """
    Detect swing highs and swing lows.

    Returns:
        DataFrame with:
        - swing_high
        - swing_low
    """

    data = df.copy()

    data["swing_high"] = False
    data["swing_low"] = False

    if len(data) < left + right + 1:
        return data

    for i in range(left, len(data) - right):

        current_high = data["high"].iloc[i]
        current_low = data["low"].iloc[i]

        left_highs = data["high"].iloc[i - left:i]
        right_highs = data["high"].iloc[i + 1:i + right + 1]

        left_lows = data["low"].iloc[i - left:i]
        right_lows = data["low"].iloc[i + 1:i + right + 1]

        if current_high > left_highs.max() and current_high > right_highs.max():
            data.iloc[i, data.columns.get_loc("swing_high")] = True

        if current_low < left_lows.min() and current_low < right_lows.min():
            data.iloc[i, data.columns.get_loc("swing_low")] = True

    return data


# ============================================================
# MARKET STRUCTURE
# ============================================================

def detect_structure(df):
    """
    Detect basic BOS and CHOCH using confirmed swing points.

    Returns:
        {
            "structure": "BULLISH" / "BEARISH" / "NEUTRAL",
            "bos": "BULLISH" / "BEARISH" / None,
            "choch": "BULLISH" / "BEARISH" / None
        }
    """

    data = find_swings(df)

    swing_highs = data[data["swing_high"]]
    swing_lows = data[data["swing_low"]]

    if len(swing_highs) < 2 or len(swing_lows) < 2:
        return {
            "structure": "NEUTRAL",
            "bos": None,
            "choch": None
        }

    last_close = float(data["close"].iloc[-1])

    previous_high = float(swing_highs["high"].iloc[-1])
    previous_low = float(swing_lows["low"].iloc[-1])

    previous_high_before = float(swing_highs["high"].iloc[-2])
    previous_low_before = float(swing_lows["low"].iloc[-2])

    bullish_structure = (
        previous_high > previous_high_before
        and previous_low > previous_low_before
    )

    bearish_structure = (
        previous_high < previous_high_before
        and previous_low < previous_low_before
    )

    bos = None
    choch = None

    # Current close breaks latest swing high
    if last_close > previous_high:
        bos = "BULLISH"

        if bearish_structure:
            choch = "BULLISH"

    # Current close breaks latest swing low
    elif last_close < previous_low:
        bos = "BEARISH"

        if bullish_structure:
            choch = "BEARISH"

    if bullish_structure:
        structure = "BULLISH"

    elif bearish_structure:
        structure = "BEARISH"

    else:
        structure = "NEUTRAL"

    return {
        "structure": structure,
        "bos": bos,
        "choch": choch
    }


# ============================================================
# LIQUIDITY SWEEP
# ============================================================

def detect_liquidity_sweep(df):
    """
    Detect possible liquidity sweeps around the latest
    confirmed swing high/low.

    Returns:
        "BULLISH"
        "BEARISH"
        None
    """

    data = find_swings(df)

    swing_highs = data[data["swing_high"]]
    swing_lows = data[data["swing_low"]]

    if swing_highs.empty and swing_lows.empty:
        return None

    last = data.iloc[-1]

    # --------------------------------------------------------
    # Bearish liquidity sweep:
    # Price takes previous high but closes back below it.
    # --------------------------------------------------------

    if not swing_highs.empty:

        last_swing_high = float(swing_highs["high"].iloc[-1])

        if (
            float(last["high"]) > last_swing_high
            and float(last["close"]) < last_swing_high
        ):
            return "BEARISH"

    # --------------------------------------------------------
    # Bullish liquidity sweep:
    # Price takes previous low but closes back above it.
    # --------------------------------------------------------

    if not swing_lows.empty:

        last_swing_low = float(swing_lows["low"].iloc[-1])

        if (
            float(last["low"]) < last_swing_low
            and float(last["close"]) > last_swing_low
        ):
            return "BULLISH"

    return None


# ============================================================
# FAIR VALUE GAP
# ============================================================

def detect_fvg(df):
    """
    Detect the latest 3-candle Fair Value Gap.

    Bullish FVG:
        candle[-3].high < candle[-1].low

    Bearish FVG:
        candle[-3].low > candle[-1].high

    Returns information about the latest FVG.
    """

    if len(df) < 3:
        return {
            "type": None,
            "upper": None,
            "lower": None,
            "size": None
        }

    data = df.reset_index(drop=True)

    c1 = data.iloc[-3]
    c3 = data.iloc[-1]

    atr = None

    if "atr" in data.columns:
        try:
            atr = float(data["atr"].iloc[-1])
        except Exception:
            atr = None

    # Bullish FVG
    bullish_gap = float(c1["high"]) < float(c3["low"])

    if bullish_gap:

        lower = float(c1["high"])
        upper = float(c3["low"])
        size = upper - lower

        if atr is None or size >= atr * FVG_MIN_SIZE_ATR:
            return {
                "type": "BULLISH",
                "upper": upper,
                "lower": lower,
                "size": size
            }

    # Bearish FVG
    bearish_gap = float(c1["low"]) > float(c3["high"])

    if bearish_gap:

        upper = float(c1["low"])
        lower = float(c3["high"])
        size = upper - lower

        if atr is None or size >= atr * FVG_MIN_SIZE_ATR:
            return {
                "type": "BEARISH",
                "upper": upper,
                "lower": lower,
                "size": size
            }

    return {
        "type": None,
        "upper": None,
        "lower": None,
        "size": None
    }


# ============================================================
# ORDER BLOCK
# ============================================================

def detect_order_block(df):
    """
    Detect a simple candidate Order Block.

    Bullish OB:
        Last bearish candle before a strong bullish move.

    Bearish OB:
        Last bullish candle before a strong bearish move.

    This is intentionally conservative.
    """

    if len(df) < 5:
        return {
            "type": None,
            "high": None,
            "low": None
        }

    data = df.reset_index(drop=True)

    last = data.iloc[-1]

    # Recent candles
    recent = data.iloc[-5:-1]

    last_close = float(last["close"])
    last_open = float(last["open"])

    # --------------------------------------------------------
    # Bullish candidate
    # --------------------------------------------------------

    if last_close > last_open:

        bearish_candidates = recent[
            recent["close"] < recent["open"]
        ]

        if not bearish_candidates.empty:

            candle = bearish_candidates.iloc[-1]

            return {
                "type": "BULLISH",
                "high": float(candle["high"]),
                "low": float(candle["low"])
            }

    # --------------------------------------------------------
    # Bearish candidate
    # --------------------------------------------------------

    if last_close < last_open:

        bullish_candidates = recent[
            recent["close"] > recent["open"]
        ]

        if not bullish_candidates.empty:

            candle = bullish_candidates.iloc[-1]

            return {
                "type": "BEARISH",
                "high": float(candle["high"]),
                "low": float(candle["low"])
            }

    return {
        "type": None,
        "high": None,
        "low": None
    }


# ============================================================
# COMPLETE SMC ANALYSIS
# ============================================================

def analyze_smc(df):
    """
    Run all SMC analysis.

    Returns a compact dictionary that other modules
    can consume safely.
    """

    if df is None or df.empty:
        return None

    required_columns = {
        "open",
        "high",
        "low",
        "close"
    }

    if not required_columns.issubset(df.columns):
        return None

    try:

        structure = detect_structure(df)

        liquidity_sweep = detect_liquidity_sweep(df)

        fvg = detect_fvg(df)

        order_block = detect_order_block(df)

        return {

            "structure": structure["structure"],

            "bos": structure["bos"],

            "choch": structure["choch"],

            "liquidity_sweep": liquidity_sweep,

            "fvg": fvg,

            "order_block": order_block

        }

    except Exception:
        return None
