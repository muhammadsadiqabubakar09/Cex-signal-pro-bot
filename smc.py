import pandas as pd


# ============================================================
# SMC ENGINE — V2
# ============================================================

SWING_LEFT = 3
SWING_RIGHT = 3

# Minimum FVG size relative to ATR.
FVG_MIN_SIZE_ATR = 0.20

# Minimum displacement candle body relative to ATR.
DISPLACEMENT_MIN_ATR = 0.80

# Minimum wick penetration beyond liquidity level.
SWEEP_MIN_ATR = 0.05


# ============================================================
# EMPTY SMC RESULT
# ============================================================

def empty_smc():
    """
    Return a safe empty SMC structure.

    Keeps compatibility with signals.py.
    """

    return {
        "structure": "NEUTRAL",

        "bos": None,

        "choch": None,

        "liquidity_sweep": None,

        "fvg": {
            "type": None,
            "upper": None,
            "lower": None,
            "size": None
        },

        "order_block": {
            "type": None,
            "high": None,
            "low": None
        },

        "displacement": None
    }


# ============================================================
# VALIDATION
# ============================================================

def validate_dataframe(df):
    """
    Validate the dataframe before SMC analysis.
    """

    if df is None or df.empty:
        return False

    required_columns = {
        "open",
        "high",
        "low",
        "close"
    }

    return required_columns.issubset(
        df.columns
    )


# ============================================================
# SWING DETECTION
# ============================================================

def find_swings(
    df,
    left=SWING_LEFT,
    right=SWING_RIGHT
):
    """
    Detect confirmed swing highs and swing lows.

    A swing is confirmed only after candles exist
    on both sides of the candidate candle.
    """

    data = df.copy()

    data["swing_high"] = False
    data["swing_low"] = False

    if len(data) < left + right + 1:
        return data

    for i in range(
        left,
        len(data) - right
    ):

        current_high = float(
            data["high"].iloc[i]
        )

        current_low = float(
            data["low"].iloc[i]
        )

        left_highs = data["high"].iloc[
            i - left:i
        ]

        right_highs = data["high"].iloc[
            i + 1:i + right + 1
        ]

        left_lows = data["low"].iloc[
            i - left:i
        ]

        right_lows = data["low"].iloc[
            i + 1:i + right + 1
        ]

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
# MARKET STRUCTURE
# ============================================================

def detect_structure(df):
    """
    Detect current market structure and confirmed
    BOS / CHOCH.

    Structure is based on the latest confirmed
    swing highs and swing lows.
    """

    data = find_swings(df)

    swing_highs = data[
        data["swing_high"]
    ]

    swing_lows = data[
        data["swing_low"]
    ]

    if (
        len(swing_highs) < 2
        or len(swing_lows) < 2
    ):

        return {
            "structure": "NEUTRAL",
            "bos": None,
            "choch": None
        }

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

    # ========================================================
    # STRUCTURE
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
    # BOS
    # ========================================================

    bos = None
    choch = None

    if last_close > latest_high:

        bos = "BULLISH"

    elif last_close < latest_low:

        bos = "BEARISH"

    # ========================================================
    # CHOCH
    # ========================================================

    if bearish_structure and last_close > latest_high:

        choch = "BULLISH"

    elif bullish_structure and last_close < latest_low:

        choch = "BEARISH"

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
    Detect meaningful liquidity sweeps.

    Bullish sweep:
        Price trades below a confirmed swing low
        and closes back above that level.

    Bearish sweep:
        Price trades above a confirmed swing high
        and closes back below that level.

    A minimum ATR penetration is required to reduce
    random wick noise.
    """

    data = find_swings(df)

    if "atr" in data.columns:

        try:
            atr = float(
                data["atr"].iloc[-1]
            )
        except Exception:
            atr = 0.0

    else:

        atr = 0.0

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

    # ========================================================
    # BEARISH LIQUIDITY SWEEP
    # ========================================================

    swing_highs = data[
        data["swing_high"]
    ]

    if not swing_highs.empty:

        level = float(
            swing_highs["high"].iloc[-1]
        )

        penetration = (
            last_high - level
        )

        minimum_penetration = (
            atr * SWEEP_MIN_ATR
        )

        if (
            penetration >= minimum_penetration
            and last_close < level
        ):

            return "BEARISH"

    # ========================================================
    # BULLISH LIQUIDITY SWEEP
    # ========================================================

    swing_lows = data[
        data["swing_low"]
    ]

    if not swing_lows.empty:

        level = float(
            swing_lows["low"].iloc[-1]
        )

        penetration = (
            level - last_low
        )

        minimum_penetration = (
            atr * SWEEP_MIN_ATR
        )

        if (
            penetration >= minimum_penetration
            and last_close > level
        ):

            return "BULLISH"

    return None


# ============================================================
# DISPLACEMENT
# ============================================================

def detect_displacement(df):
    """
    Detect strong directional displacement.

    A displacement candle must have a body
    large enough relative to ATR.
    """

    if len(df) < 2:
        return None

    last = df.iloc[-1]

    try:

        open_price = float(
            last["open"]
        )

        close_price = float(
            last["close"]
        )

        atr = float(
            last["atr"]
        ) if "atr" in df.columns else 0.0

    except Exception:

        return None

    if atr <= 0:
        return None

    body = abs(
        close_price - open_price
    )

    body_ratio = body / atr

    if body_ratio < DISPLACEMENT_MIN_ATR:
        return None

    if close_price > open_price:

        return "BULLISH"

    if close_price < open_price:

        return "BEARISH"

    return None


# ============================================================
# FAIR VALUE GAP
# ============================================================

def detect_fvg(df):
    """
    Detect the latest three-candle Fair Value Gap.

    Requires:
        - Actual price imbalance
        - Minimum ATR size
        - Directional displacement
    """

    empty = {
        "type": None,
        "upper": None,
        "lower": None,
        "size": None
    }

    if len(df) < 3:
        return empty

    data = df.reset_index(
        drop=True
    )

    first = data.iloc[-3]
    middle = data.iloc[-2]
    last = data.iloc[-1]

    try:

        first_high = float(
            first["high"]
        )

        first_low = float(
            first["low"]
        )

        middle_open = float(
            middle["open"]
        )

        middle_close = float(
            middle["close"]
        )

        last_high = float(
            last["high"]
        )

        last_low = float(
            last["low"]
        )

        atr = float(
            last["atr"]
        ) if "atr" in data.columns else 0.0

    except Exception:

        return empty

    if atr <= 0:
        return empty

    # ========================================================
    # BULLISH FVG
    # ========================================================

    if first_high < last_low:

        lower = first_high
        upper = last_low

        size = upper - lower

        middle_body = abs(
            middle_close - middle_open
        )

        bullish_middle = (
            middle_close > middle_open
        )

        displacement = (
            middle_body >= atr * DISPLACEMENT_MIN_ATR
        )

        if (
            bullish_middle
            and displacement
            and size >= atr * FVG_MIN_SIZE_ATR
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

    if first_low > last_high:

        upper = first_low
        lower = last_high

        size = upper - lower

        middle_body = abs(
            middle_close - middle_open
        )

        bearish_middle = (
            middle_close < middle_open
        )

        displacement = (
            middle_body >= atr * DISPLACEMENT_MIN_ATR
        )

        if (
            bearish_middle
            and displacement
            and size >= atr * FVG_MIN_SIZE_ATR
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

def detect_order_block(df):
    """
    Detect a recent Order Block candidate.

    The Order Block must be an opposing candle
    immediately preceding a strong displacement candle.

    This is stricter than simply selecting any
    recent bullish/bearish candle.
    """

    empty = {
        "type": None,
        "high": None,
        "low": None
    }

    if len(df) < 5:
        return empty

    data = df.reset_index(
        drop=True
    )

    displacement = detect_displacement(
        data
    )

    if displacement is None:
        return empty

    displacement_candle = data.iloc[-1]
    previous_candle = data.iloc[-2]

    displacement_open = float(
        displacement_candle["open"]
    )

    displacement_close = float(
        displacement_candle["close"]
    )

    previous_open = float(
        previous_candle["open"]
    )

    previous_close = float(
        previous_candle["close"]
    )

    # ========================================================
    # BULLISH ORDER BLOCK
    # ========================================================

    if displacement == "BULLISH":

        if previous_close < previous_open:

            return {
                "type": "BULLISH",
                "high": float(
                    previous_candle["high"]
                ),
                "low": float(
                    previous_candle["low"]
                )
            }

    # ========================================================
    # BEARISH ORDER BLOCK
    # ========================================================

    if displacement == "BEARISH":

        if previous_close > previous_open:

            return {
                "type": "BEARISH",
                "high": float(
                    previous_candle["high"]
                ),
                "low": float(
                    previous_candle["low"]
                )
            }

    return empty


# ============================================================
# COMPLETE SMC ANALYSIS
# ============================================================

def analyze_smc(df):
    """
    Run the complete SMC V2 analysis.

    Returns:
        structure
        BOS
        CHOCH
        liquidity sweep
        FVG
        Order Block
        displacement
    """

    if not validate_dataframe(df):

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

        displacement = detect_displacement(
            df
        )

        return {

            "structure":
                structure["structure"],

            "bos":
                structure["bos"],

            "choch":
                structure["choch"],

            "liquidity_sweep":
                liquidity_sweep,

            "fvg":
                fvg,

            "order_block":
                order_block,

            "displacement":
                displacement
        }

    except Exception:

        return empty_smc()