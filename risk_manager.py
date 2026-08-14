from typing import Dict


# ============================================================
# RISK CONFIGURATION
# ============================================================

SL_ATR_MULTIPLIER = 1.5

TP1_RR = 1.5
TP2_RR = 2.5
TP3_RR = 4.0

MIN_RISK_REWARD = 1.5


# ============================================================
# MAIN TRADE CALCULATOR
# ============================================================

def calculate_trade(
    price: float,
    atr: float,
    signal_data: Dict
):
    """
    Calculate Entry, Stop Loss, Take Profit,
    Risk/Reward and Suggested Leverage.

    This function is compatible with the output
    produced by signals.py.
    """

    # ========================================================
    # VALIDATION
    # ========================================================

    if price <= 0:
        return {}

    if atr <= 0:
        return {}

    direction = signal_data.get("direction")
    market = signal_data.get("market")
    confidence = signal_data.get("confidence")

    if direction not in ["BUY", "LONG", "SHORT"]:
        return {}

    if market not in ["SPOT", "FUTURES"]:
        return {}

    # ========================================================
    # ENTRY
    # ========================================================

    entry = float(price)

    # ========================================================
    # STOP LOSS
    # ========================================================

    risk_distance = atr * SL_ATR_MULTIPLIER

    if direction in ["BUY", "LONG"]:

        stop_loss = entry - risk_distance

    elif direction == "SHORT":

        stop_loss = entry + risk_distance

    else:
        return {}

    # ========================================================
    # RISK
    # ========================================================

    risk = abs(entry - stop_loss)

    if risk <= 0:
        return {}

    # ========================================================
    # TAKE PROFITS
    # ========================================================

    if direction in ["BUY", "LONG"]:

        tp1 = entry + (risk * TP1_RR)
        tp2 = entry + (risk * TP2_RR)
        tp3 = entry + (risk * TP3_RR)

    elif direction == "SHORT":

        tp1 = entry - (risk * TP1_RR)
        tp2 = entry - (risk * TP2_RR)
        tp3 = entry - (risk * TP3_RR)

    else:
        return {}

    # ========================================================
    # RISK / REWARD
    # ========================================================

    reward = abs(tp2 - entry)

    if reward <= 0:
        return {}

    risk_reward = reward / risk

    if risk_reward < MIN_RISK_REWARD:
        return {}

    risk_percent = (risk / entry) * 100

    reward_percent = (reward / entry) * 100

    # ========================================================
    # LEVERAGE
    # ========================================================

    if market == "SPOT":

        leverage = "None"

    elif confidence == "VERY HIGH":

        leverage = "5x"

    elif confidence == "HIGH":

        leverage = "3x"

    elif confidence == "MEDIUM":

        leverage = "2x"

    else:

        leverage = "None"

    # ========================================================
    # RETURN
    # ========================================================

    return {

        "market": market,

        "direction": direction,

        "entry": round(entry, 8),

        "stop_loss": round(stop_loss, 8),

        "tp1": round(tp1, 8),
        "tp2": round(tp2, 8),
        "tp3": round(tp3, 8),

        "risk_percent": round(risk_percent, 2),

        "reward_percent": round(reward_percent, 2),

        "risk_reward": round(risk_reward, 2),

        "suggested_leverage": leverage
    }