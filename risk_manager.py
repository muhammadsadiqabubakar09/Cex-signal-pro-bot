from typing import Dict


# ============================================================
# RISK MANAGER V2
# ============================================================

# ------------------------------------------------------------
# STOP LOSS
# ------------------------------------------------------------

MIN_SL_ATR = 1.5
DEFAULT_SL_ATR = 1.8
MAX_SL_ATR = 3.0

# ------------------------------------------------------------
# TAKE PROFIT
# ------------------------------------------------------------

TP1_RR = 1.5
TP2_RR = 2.5
TP3_RR = 4.0

# ------------------------------------------------------------
# TRADE QUALITY
# ------------------------------------------------------------

MIN_RISK_REWARD = 2.0
MAX_RISK_PERCENT = 6.0


# ============================================================
# HELPERS
# ============================================================

def safe_float(value, default=None):
    """
    Safely convert a value to float.
    """

    try:
        return float(value)

    except (TypeError, ValueError):

        return default


# ============================================================
# MAIN TRADE CALCULATOR
# ============================================================

def calculate_trade(
    price: float,
    atr: float,
    signal_data: Dict
):
    """
    Calculate a complete trade setup.

    Pipeline:

        Entry
          ↓
        ATR-based SL
          ↓
        Actual Risk
          ↓
        TP1 / TP2 / TP3
          ↓
        RR Validation
          ↓
        Trade Quality Check
    """

    # ========================================================
    # VALIDATION
    # ========================================================

    entry = safe_float(
        price
    )

    atr = safe_float(
        atr
    )

    if entry is None or entry <= 0:
        return {}

    if atr is None or atr <= 0:
        return {}

    if not isinstance(
        signal_data,
        dict
    ):
        return {}

    direction = str(
        signal_data.get(
            "direction",
            ""
        )
    ).upper()

    market = str(
        signal_data.get(
            "market",
            ""
        )
    ).upper()

    confidence = str(
        signal_data.get(
            "confidence",
            ""
        )
    ).upper()

    if direction not in [
        "BUY",
        "LONG",
        "SHORT"
    ]:
        return {}

    if market not in [
        "SPOT",
        "FUTURES"
    ]:
        return {}

    # ========================================================
    # ATR STOP DISTANCE
    # ========================================================

    risk_distance = (
        atr * DEFAULT_SL_ATR
    )

    minimum_distance = (
        atr * MIN_SL_ATR
    )

    maximum_distance = (
        atr * MAX_SL_ATR
    )

    # --------------------------------------------------------
    # Protect against abnormal ATR values
    # --------------------------------------------------------

    if risk_distance < minimum_distance:

        risk_distance = minimum_distance

    if risk_distance > maximum_distance:

        risk_distance = maximum_distance

    # ========================================================
    # STOP LOSS
    # ========================================================

    if direction in [
        "BUY",
        "LONG"
    ]:

        stop_loss = (
            entry - risk_distance
        )

    elif direction == "SHORT":

        stop_loss = (
            entry + risk_distance
        )

    else:

        return {}

    # ========================================================
    # ACTUAL RISK
    # ========================================================

    risk = abs(
        entry - stop_loss
    )

    if risk <= 0:
        return {}

    # ========================================================
    # RISK PERCENTAGE
    # ========================================================

    risk_percent = (
        risk / entry
    ) * 100

    # --------------------------------------------------------
    # Reject excessively wide stop
    # --------------------------------------------------------

    if risk_percent > MAX_RISK_PERCENT:

        return {}

    # ========================================================
    # TAKE PROFITS
    # ========================================================

    if direction in [
        "BUY",
        "LONG"
    ]:

        tp1 = entry + (
            risk * TP1_RR
        )

        tp2 = entry + (
            risk * TP2_RR
        )

        tp3 = entry + (
            risk * TP3_RR
        )

    elif direction == "SHORT":

        tp1 = entry - (
            risk * TP1_RR
        )

        tp2 = entry - (
            risk * TP2_RR
        )

        tp3 = entry - (
            risk * TP3_RR
        )

    else:

        return {}

    # ========================================================
    # VALIDATE TP ORDER
    # ========================================================

    if direction in [
        "BUY",
        "LONG"
    ]:

        if not (
            tp1 > entry
            and tp2 > tp1
            and tp3 > tp2
        ):
            return {}

    elif direction == "SHORT":

        if not (
            tp1 < entry
            and tp2 < tp1
            and tp3 < tp2
        ):
            return {}

    # ========================================================
    # RISK / REWARD
    # ========================================================

    reward_tp1 = abs(
        tp1 - entry
    )

    reward_tp2 = abs(
        tp2 - entry
    )

    reward_tp3 = abs(
        tp3 - entry
    )

    rr_tp1 = (
        reward_tp1 / risk
    )

    rr_tp2 = (
        reward_tp2 / risk
    )

    rr_tp3 = (
        reward_tp3 / risk
    )

    # --------------------------------------------------------
    # Minimum RR validation
    # --------------------------------------------------------

    if rr_tp2 < MIN_RISK_REWARD:

        return {}

    # ========================================================
    # REWARD PERCENTAGES
    # ========================================================

    tp1_percent = (
        reward_tp1 / entry
    ) * 100

    tp2_percent = (
        reward_tp2 / entry
    ) * 100

    tp3_percent = (
        reward_tp3 / entry
    ) * 100

    # ========================================================
    # LEVERAGE
    # ========================================================

    if market == "SPOT":

        leverage = "None"

    elif confidence == "VERY HIGH":

        leverage = "3x"

    elif confidence == "HIGH":

        leverage = "2x"

    else:

        leverage = "None"

    # ========================================================
    # ROUNDING
    # ========================================================

    entry = round(
        entry,
        8
    )

    stop_loss = round(
        stop_loss,
        8
    )

    tp1 = round(
        tp1,
        8
    )

    tp2 = round(
        tp2,
        8
    )

    tp3 = round(
        tp3,
        8
    )

    # ========================================================
    # FINAL RETURN
    # ========================================================

    return {

        "market":
            market,

        "direction":
            direction,

        "entry":
            entry,

        "stop_loss":
            stop_loss,

        "tp1":
            tp1,

        "tp2":
            tp2,

        "tp3":
            tp3,

        "risk_percent":
            round(
                risk_percent,
                2
            ),

        "tp1_percent":
            round(
                tp1_percent,
                2
            ),

        "tp2_percent":
            round(
                tp2_percent,
                2
            ),

        "tp3_percent":
            round(
                tp3_percent,
                2
            ),

        "risk_reward":
            round(
                rr_tp2,
                2
            ),

        "tp1_rr":
            round(
                rr_tp1,
                2
            ),

        "tp2_rr":
            round(
                rr_tp2,
                2
            ),

        "tp3_rr":
            round(
                rr_tp3,
                2
            ),

        "suggested_leverage":
            leverage
    }