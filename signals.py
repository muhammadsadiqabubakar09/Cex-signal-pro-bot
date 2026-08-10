from typing import Dict


def generate_signal(mtf_data: Dict):
    """
    Professional Multi-Timeframe Signal Generator
    """

    score = 0
    reasons = []

    tf5 = mtf_data["5m"]
    tf15 = mtf_data["15m"]
    tf1h = mtf_data["1h"]
    tf4h = mtf_data["4h"]

    signal = "⚪ NO TRADE"
    market = "NONE"
    direction = "NONE"
    confidence = "LOW"

    # ==========================
    # TREND (45)
    # ==========================

    bullish = (
        tf4h["ema20"] > tf4h["ema50"] > tf4h["ema200"] and
        tf1h["ema20"] > tf1h["ema50"] > tf1h["ema200"]
    )

    bearish = (
        tf4h["ema20"] < tf4h["ema50"] < tf4h["ema200"] and
        tf1h["ema20"] < tf1h["ema50"] < tf1h["ema200"]
    )

    if bullish:
        score += 30
        reasons.append("4H & 1H Bullish Trend")

    elif bearish:
        score += 30
        reasons.append("4H & 1H Bearish Trend")

    if bullish and tf15["ema20"] > tf15["ema50"]:
        score += 10
        reasons.append("15M Bullish Confirmation")

    elif bearish and tf15["ema20"] < tf15["ema50"]:
        score += 10
        reasons.append("15M Bearish Confirmation")

    if bullish and tf5["ema20"] > tf5["ema50"]:
        score += 5
        reasons.append("5M Entry")

    elif bearish and tf5["ema20"] < tf5["ema50"]:
        score += 5
        reasons.append("5M Entry")

    # ==========================
    # MOMENTUM (35)
    # ==========================

    if bullish:

        if 55 <= tf5["rsi"] <= 70:
            score += 8
            reasons.append("Healthy RSI")

        if tf5["macd"] > tf5["macd_signal"]:
            score += 8
            reasons.append("Bullish MACD")

        if tf5["macd_hist"] > 0:
            score += 4
            reasons.append("Positive MACD Histogram")

        if tf5["stoch_rsi_k"] > tf5["stoch_rsi_d"]:
            score += 5
            reasons.append("Stoch RSI Confirmation")

    elif bearish:

        if 30 <= tf5["rsi"] <= 45:
            score += 8
            reasons.append("Bearish RSI")

        if tf5["macd"] < tf5["macd_signal"]:
            score += 8
            reasons.append("Bearish MACD")

        if tf5["macd_hist"] < 0:
            score += 4
            reasons.append("Negative MACD Histogram")

        if tf5["stoch_rsi_k"] < tf5["stoch_rsi_d"]:
            score += 5
            reasons.append("Stoch RSI Confirmation")

    if tf5["adx"] >= 25:
        score += 10
        reasons.append("Strong ADX")

    # ==========================
    # CONFIRMATION (20)
    # ==========================

    if tf5["volume"] > tf5["volume_sma"]:
        score += 5
        reasons.append("High Volume")

    if bullish and tf5["close"] > tf5["vwap"]:
        score += 5
        reasons.append("Above VWAP")

    elif bearish and tf5["close"] < tf5["vwap"]:
        score += 5
        reasons.append("Below VWAP")

    if bullish and tf5["close"] > tf5["bb_middle"]:
        score += 5
        reasons.append("Above Bollinger")

    elif bearish and tf5["close"] < tf5["bb_middle"]:
        score += 5
        reasons.append("Below Bollinger")

    if tf5["atr"] > 0:
        score += 5
        reasons.append("ATR Confirmed")

    # ==========================
    # FINAL DECISION
    # ==========================

    if bullish:

        if score >= 95:
            signal = "🔥 ELITE LONG"
            market = "FUTURES"
            direction = "LONG"
            confidence = "VERY HIGH"

        elif score >= 90:
            signal = "🟢 STRONG LONG"
            market = "FUTURES"
            direction = "LONG"
            confidence = "HIGH"

        elif score >= 80:
            signal = "🟢 BUY"
            market = "SPOT"
            direction = "BUY"
            confidence = "MEDIUM"

    elif bearish:

        if score >= 95:
            signal = "🔥 ELITE SHORT"
            market = "FUTURES"
            direction = "SHORT"
            confidence = "VERY HIGH"

        elif score >= 90:
            signal = "🔴 STRONG SHORT"
            market = "FUTURES"
            direction = "SHORT"
            confidence = "HIGH"

    return {
        "signal": signal,
        "market": market,
        "direction": direction,
        "score": score,
        "confidence": confidence,
        "reasons": reasons
    }