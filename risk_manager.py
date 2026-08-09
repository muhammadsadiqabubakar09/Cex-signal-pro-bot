from typing import Dict


def calculate_trade(price: float, atr: float, signal_data: Dict):
    """
    Calculate Entry, Stop Loss, Take Profit,
    Risk/Reward and Suggested Leverage.
    """

    # =========================
    # VALIDATION
    # =========================

    if price <= 0:
        return {}

    if atr <= 0:
        return {}

    direction = signal_data["direction"]
    market = signal_data["market"]
    confidence = signal_data["confidence"]

    if direction == "NONE":
        return {}

    # =========================
    # STOP LOSS & TAKE PROFIT
    # =========================

    if direction in ["BUY", "LONG"]:

        stop_loss = price - (1.5 * atr)

        tp1 = price + (2 * atr)
        tp2 = price + (3 * atr)
        tp3 = price + (4 * atr)

    elif direction == "SHORT":

        stop_loss = price + (1.5 * atr)

        tp1 = price - (2 * atr)
        tp2 = price - (3 * atr)
        tp3 = price - (4 * atr)

    else:
        return {}

    # =========================
    # RISK CALCULATION
    # =========================

    risk = abs(price - stop_loss)
    reward = abs(tp2 - price)

    risk_percent = round((risk / price) * 100, 2)
    reward_percent = round((reward / price) * 100, 2)

    risk_reward = round(reward / risk, 2)

    # =========================
    # LEVERAGE
    # =========================

    if market == "SPOT":
        leverage = "None"

    else:

        if confidence == "VERY HIGH":
            leverage = "5x"

        elif confidence == "HIGH":
            leverage = "3x"

        elif confidence == "MEDIUM":
            leverage = "2x"

        else:
            leverage = "None"

    # =========================
    # RETURN
    # =========================

    return {

        "market": market,

        "direction": direction,

        "entry": round(price, 6),

        "stop_loss": round(stop_loss, 6),

        "tp1": round(tp1, 6),
        "tp2": round(tp2, 6),
        "tp3": round(tp3, 6),

        "risk_percent": risk_percent,
        "reward_percent": reward_percent,

        "risk_reward": risk_reward,

        "suggested_leverage": leverage
    }