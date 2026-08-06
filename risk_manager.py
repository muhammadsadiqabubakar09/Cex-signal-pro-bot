from typing import Dict


def calculate_trade(price: float, signal: str) -> Dict:

    if signal == "BUY":

        stop_loss = price * 0.98
        tp1 = price * 1.02
        tp2 = price * 1.04
        tp3 = price * 1.06

    elif signal == "SELL":

        stop_loss = price * 1.02
        tp1 = price * 0.98
        tp2 = price * 0.96
        tp3 = price * 0.94

    else:
        return {}

    risk = abs(price - stop_loss)
    reward = abs(tp2 - price)

    rr = round(reward / risk, 2)

    return {
        "entry": round(price, 4),
        "stop_loss": round(stop_loss, 4),
        "tp1": round(tp1, 4),
        "tp2": round(tp2, 4),
        "tp3": round(tp3, 4),
        "risk_reward": rr,
    }
