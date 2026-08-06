from typing import Dict, List


def calculate_score(data: Dict):

    score = 0
    reasons: List[str] = []

    # EMA
    if data.get("ema"):
        score += 15
        reasons.append("EMA Trend Confirmed")

    # RSI
    if data.get("rsi"):
        score += 10
        reasons.append("RSI Healthy")

    # Volume
    if data.get("volume"):
        score += 10
        reasons.append("High Volume")

    # Trend
    if data.get("trend"):
        score += 20
        reasons.append("Trend Confirmed")

    # Multi Timeframe
    if data.get("mtf"):
        score += 20
        reasons.append("Multi-Timeframe Confirmed")

    # Risk Reward
    if data.get("rr"):
        score += 15
        reasons.append("Good Risk Reward")

    # Price Action
    if data.get("price_action"):
        score += 10
        reasons.append("Price Action Confirmed")

    return score, reasons


def generate_signal(data: Dict):

    score, reasons = calculate_score(data)

    if score >= 90:
        signal = "STRONG BUY"

    elif score >= 80:
        signal = "BUY"

    else:
        signal = None

    return {
        "signal": signal,
        "score": score,
        "reasons": reasons,
    }
