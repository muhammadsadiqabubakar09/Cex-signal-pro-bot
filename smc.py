import pandas as pd


# ============================================================
# SMC CONFIGURATION
# ============================================================

SWING_LEFT = 3
SWING_RIGHT = 3

FVG_MIN_SIZE_ATR = 0.10


# ============================================================
# EMPTY SMC RESULT
# ============================================================

def empty_smc():
    """
    Return a safe empty SMC structure.

    This guarantees compatibility with signals.py.
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
        }
    }


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

        if (
            current_high > left_highs.max()
            and current_high > right_highs.max()
        ):
            data.at[
                data.index[i],
                "swing_high"
            ] = True

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
    Detect market structure, BOS and CHOCH.
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

    last_close = float(
        data["close"].iloc[-1]
    )

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

    bos = None
    choch = None

    # --------------------------------------------------------
    # Bullish break
    # --------------------------------------------------------

    if last_close > latest_high:

        bos = "BULLISH"

        if bearish_structure:
            choch = "BULLISH"

    # --------------------------------------------------------
    # Bearish break
    # --------------------------------------------------------

    elif last_close < latest_low:

        bos = "BEARISH"

        if bullish_structure:
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
    Detect bullish or bearish liquidity sweep.
    """

    data = find_swings(df)

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

    last = data.iloc[-1]

    # --------------------------------------------------------
    # Bearish sweep
    # --------------------------------------------------------

    if not swing_highs.empty:

        level = float(
            swing_highs["high"].iloc[-1]
        )

        if (
            float(last["high"]) > level
            and float(last["close"]) < level
        ):
            return "BEARISH"

    # --------------------------------------------------------
    # Bullish sweep
    # --------------------------------------------------------

    if not swing_lows.empty:

        level = float(
            swing_lows["low"].iloc[-1]
        )

        if (
            float(last["low"]) < level
            and float(last["close"]) > level
        ):
            return "BULLISH"

    return None


# ============================================================
# FAIR VALUE GAP
# ============================================================

def detect_fvg(df):
    """
    Detect the latest three-candle Fair Value Gap.
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
    last = data.iloc[-1]

    try:

        first_high = float(
            first["high"]
        )

        first_low = float(
            first["low"]
        )

        last_high = float(
            last["high"]
        )

        last_low = float(
            last["low"]
        )

    except Exception:

        return empty

    atr = None

    if "atr" in data.columns:

        try:
            atr = float(
                data["atr"].iloc[-1]
            )
        except Exception:
            atr = None

    # --------------------------------------------------------
    # Bullish FVG
    # --------------------------------------------------------

    if first_high < last_low:

        lower = first_high
        upper = last_low
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

    # --------------------------------------------------------
    # Bearish FVG
    # --------------------------------------------------------

    if first_low > last_high:

        upper = first_low
        lower = last_high
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

def detect_order_block(df):
    """
    Detect a simple recent Order Block candidate.
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

    last = data.iloc[-1]

    recent = data.iloc[-5:-1]

    last_open = float(
        last["open"]
    )

    last_close = float(
        last["close"]
    )

    # --------------------------------------------------------
    # Bullish Order Block
    # --------------------------------------------------------

    if last_close > last_open:

        candidates = recent[
            recent["close"]
            < recent["open"]
        ]

        if not candidates.empty:

            candle = candidates.iloc[-1]

            return {
                "type": "BULLISH",
                "high": float(
                    candle["high"]
                ),
                "low": float(
                    candle["low"]
                )
            }

    # --------------------------------------------------------
    # Bearish Order Block
    # --------------------------------------------------------

    if last_close < last_open:

        candidates = recent[
            recent["close"]
            > recent["open"]
        ]

        if not candidates.empty:

            candle = candidates.iloc[-1]

            return {
                "type": "BEARISH",
                "high": float(
                    candle["high"]
                ),
                "low": float(
                    candle["low"]
                )
            }

    return empty


# ============================================================
# COMPLETE SMC ANALYSIS
# ============================================================

def analyze_smc(df):
    """
    Run the SMC components required by signals.py.

    Output keys are kept exactly compatible with
    the current signal engine.
    """

    if df is None or df.empty:
        return empty_smc()

    required_columns = {
        "open",
        "high",
        "low",
        "close"
    }

    if not required_columns.issubset(
        df.columns
    ):
        return empty_smc()

    try:

        structure = detect_structure(
            df
        )

        liquidity_sweep = (
            detect_liquidity_sweep(df)
        )

        fvg = detect_fvg(df)

        order_block = (
            detect_order_block(df)
        )

        return {
            "structure": structure[
                "structure"
            ],

            "bos": structure[
                "bos"
            ],

            "choch": structure[
                "choch"
            ],

            "liquidity_sweep":
                liquidity_sweep,

            "fvg": fvg,

            "order_block":
                order_block
        }

    except Exception:

        return empty_smc()