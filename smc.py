from typing import Dict


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

    The output remains compatible with signals.py
    while also exposing structure price levels.
    """

    return {
        "structure": "NEUTRAL",

        "bos": None,

        "choch": None,

        "liquidity_sweep": None,

        # ----------------------------------------------------
        # Structure price levels
        # ----------------------------------------------------

        "swing_high": None,

        "previous_swing_high": None,

        "swing_low": None,

        "previous_swing_low": None,

        # ----------------------------------------------------
        # Fair Value Gap
        # ----------------------------------------------------

        "fvg": {
            "type": None,
            "upper": None,
            "lower": None,
            "size": None
        },

        # ----------------------------------------------------
        # Order Block
        # ----------------------------------------------------

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

    A swing is confirmed only after the required candles
    on both sides exist.
    """

    data = df.copy()

    data["swing_high"] = False
    data["swing_low"] = False

    minimum_length = (
        left
        + right
        + 1
    )

    if len(data) < minimum_length:

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

        left_highs = data[
            "high"
        ].iloc[
            i - left:i
        ]

        right_highs = data[
            "high"
        ].iloc[
            i + 1:i + right + 1
        ]

        left_lows = data[
            "low"
        ].iloc[
            i - left:i
        ]

        right_lows = data[
            "low"
        ].iloc[
            i + 1:i + right + 1
        ]

        # ----------------------------------------------------
        # Swing high
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
        # Swing low
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

def get_structure_levels(df):
    """
    Return the latest confirmed swing levels.

    These levels are later used by risk_manager.py
    to build structure-aware stop losses.
    """

    data = find_swings(
        df
    )

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

    # --------------------------------------------------------
    # Swing highs
    # --------------------------------------------------------

    if len(swing_highs) >= 1:

        latest_swing_high = float(
            swing_highs[
                "high"
            ].iloc[-1]
        )

    if len(swing_highs) >= 2:

        previous_swing_high = float(
            swing_highs[
                "high"
            ].iloc[-2]
        )

    # --------------------------------------------------------
    # Swing lows
    # --------------------------------------------------------

    if len(swing_lows) >= 1:

        latest_swing_low = float(
            swing_lows[
                "low"
            ].iloc[-1]
        )

    if len(swing_lows) >= 2:

        previous_swing_low = float(
            swing_lows[
                "low"
            ].iloc[-2]
        )

    return {
        "swing_high":
            latest_swing_high,

        "previous_swing_high":
            previous_swing_high,

        "swing_low":
            latest_swing_low,

        "previous_swing_low":
            previous_swing_low
    }


# ============================================================
# MARKET STRUCTURE
# ============================================================

def detect_structure(df):
    """
    Detect:

        - Bullish structure
        - Bearish structure
        - BOS
        - CHOCH

    Also returns confirmed swing price levels.
    """

    data = find_swings(
        df
    )

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

    last_close = float(
        data["close"].iloc[-1]
    )

    latest_high = float(
        swing_highs[
            "high"
        ].iloc[-1]
    )

    previous_high = float(
        swing_highs[
            "high"
        ].iloc[-2]
    )

    latest_low = float(
        swing_lows[
            "low"
        ].iloc[-1]
    )

    previous_low = float(
        swing_lows[
            "low"
        ].iloc[-2]
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
    # BOS / CHOCH
    # ========================================================

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

        "structure":
            structure,

        "bos":
            bos,

        "choch":
            choch,

        "swing_high":
            levels["swing_high"],

        "previous_swing_high":
            levels["previous_swing_high"],

        "swing_low":
            levels["swing_low"],

        "previous_swing_low":
            levels["previous_swing_low"]
    }


# ============================================================
# LIQUIDITY SWEEP
# ============================================================

def detect_liquidity_sweep(df):
    """
    Detect liquidity sweeps around confirmed swing levels.
    """

    data = find_swings(
        df
    )

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
    # Bearish liquidity sweep
    # ========================================================

    if not swing_highs.empty:

        level = float(
            swing_highs[
                "high"
            ].iloc[-1]
        )

        if (
            last_high > level
            and last_close < level
        ):

            return "BEARISH"

    # ========================================================
    # Bullish liquidity sweep
    # ========================================================

    if not swing_lows.empty:

        level = float(
            swing_lows[
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

    except (
        TypeError,
        ValueError
    ):

        return empty

    atr = None

    if "atr" in data.columns:

        try:

            atr = float(
                data["atr"].iloc[-1]
            )

        except (
            TypeError,
            ValueError
        ):

            atr = None

    # ========================================================
    # Bullish FVG
    # ========================================================

    if first_high < last_low:

        lower = first_high

        upper = last_low

        size = (
            upper
            - lower
        )

        if (
            atr is None
            or size >= (
                atr
                * FVG_MIN_SIZE_ATR
            )
        ):

            return {
                "type": "BULLISH",
                "upper": upper,
                "lower": lower,
                "size": size
            }

    # ========================================================
    # Bearish FVG
    # ========================================================

    if first_low > last_high:

        upper = first_low

        lower = last_high

        size = (
            upper
            - lower
        )

        if (
            atr is None
            or size >= (
                atr
                * FVG_MIN_SIZE_ATR
            )
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

    This is a conservative candidate detector.
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

    # ========================================================
    # Bullish Order Block
    # ========================================================

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

    # ========================================================
    # Bearish Order Block
    # ========================================================

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
    Run the complete SMC engine.

    Output includes:

        Structure
        BOS
        CHOCH
        Liquidity Sweep
        Swing High
        Previous Swing High
        Swing Low
        Previous Swing Low
        FVG
        Order Block
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
            detect_liquidity_sweep(
                df
            )
        )

        fvg = detect_fvg(
            df
        )

        order_block = (
            detect_order_block(
                df
            )
        )

        return {

            "structure":
                structure[
                    "structure"
                ],

            "bos":
                structure[
                    "bos"
                ],

            "choch":
                structure[
                    "choch"
                ],

            "liquidity_sweep":
                liquidity_sweep,

            # ------------------------------------------------
            # Structure levels
            # ------------------------------------------------

            "swing_high":
                structure[
                    "swing_high"
                ],

            "previous_swing_high":
                structure[
                    "previous_swing_high"
                ],

            "swing_low":
                structure[
                    "swing_low"
                ],

            "previous_swing_low":
                structure[
                    "previous_swing_low"
                ],

            # ------------------------------------------------
            # FVG
            # ------------------------------------------------

            "fvg":
                fvg,

            # ------------------------------------------------
            # Order Block
            # ------------------------------------------------

            "order_block":
                order_block
        }

    except Exception:

        return empty_smc()