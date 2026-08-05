import ta

def add_indicators(df):

    df["ema20"] = ta.trend.ema_indicator(
        df["close"],
        window=20
    )

    df["ema50"] = ta.trend.ema_indicator(
        df["close"],
        window=50
    )

    df["rsi"] = ta.momentum.rsi(
        df["close"],
        window=14
    )

    return df


def analyze(df):

    last = df.iloc[-1]

    score = 0
    reasons = []

    # EMA Trend
    if last.ema20 > last.ema50:
        score += 30
        reasons.append("EMA Bullish")

    # RSI
    if 50 <= last.rsi <= 70:
        score += 20
        reasons.append("Healthy RSI")

    # Volume
    if last.volume > df["volume"].mean():
        score += 20
        reasons.append("High Volume")

    if score >= 70:
        return {
            "signal": "BUY",
            "score": score,
            "reasons": reasons
        }

    return None
