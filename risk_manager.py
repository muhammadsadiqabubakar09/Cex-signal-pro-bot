from typing import Dict


def calculate_trade(price: float, atr: float, signal_data: Dict):

    direction = signal_data["direction"]
    confidence = signal_data["confidence"]

    if direction == "BUY":

        stop_loss = price - (1.5 * atr)

        tp1 = price + (2 * atr)
        tp2 = price + (3 * atr)
        tp3 = price + (4 * atr)

    elif direction == "LONG":

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

    risk = abs(price - stop_loss)
    reward = abs(tp2 - price)

    risk_percent = round((risk / price) * 100, 2)
    reward_percent = round((reward / price) * 100, 2)

    risk_reward = round(reward / risk, 2)

    # Suggested Leverage
    if confidence == "VERY HIGH":
        leverage = "3x"

    elif confidence == "HIGH":
        leverage = "4x"

    elif confidence == "MEDIUM":
        leverage = "5x"

    else:
        leverage = "-"

    return {

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