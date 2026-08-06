from typing import Dict


def generate_signal(mtf_data: Dict):

    score = 0
    reasons = []

    tf5 = mtf_data["5m"]
    tf15 = mtf_data["15m"]
    tf1h = mtf_data["1h"]

    # ===== TREND =====
    if tf1h["ema20"] > tf1h["ema50"]:
        score += 20
        reasons.append("1H Uptrend")

    if tf15["ema20"] > tf15["ema50"]:
        score += 15
        reasons.append("15M Uptrend")

    if tf5["ema20"] > tf5["ema50"]:
        score += 10
        reasons.append("5M Entry Trend")

    # ===== RSI =====
    if 50 <= tf5["rsi"] <= 70:
        score += 10
        reasons.append("Healthy RSI")

    # ===== MACD =====
    if tf5["macd"] > tf5["macd_signal"]:
        score += 10
        reasons.append("Bullish MACD")

    # ===== ADX =====
    if tf5["adx"] >= 25:
        score += 10
        reasons.append("Strong Trend")

    # ===== VOLUME =====
    if tf5["volume"] > tf5["volume_sma"]:
        score += 10
        reasons.append("High Volume")

    # ===== BOLLINGER =====
    if tf5["close"] > tf5["bb_middle"]:
        score += 5
        reasons.append("Above Bollinger Middle")

    # ===== ATR =====
    if tf5["atr"] > 0:
        score += 5
        reasons.append("ATR Confirmed")

    # ===== SIGNAL =====
    if score >= 95:
        signal = "🔥 ELITE BUY"

    elif score >= 90:
        signal = "🟢 STRONG BUY"

    elif score >= 80:
        signal = "🟢 BUY"

    elif score >= 65:
        signal = "🟡 WATCH"

    else:
        signal = "⚪ NO TRADE"

    return {
        "signal": signal,
        "score": score,
        "reasons": reasons
    }
