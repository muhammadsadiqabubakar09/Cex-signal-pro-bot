import ta


def add_indicators(df):

    # EMA
    df["ema20"] = ta.trend.ema_indicator(df["close"], window=20)
    df["ema50"] = ta.trend.ema_indicator(df["close"], window=50)

    # RSI
    df["rsi"] = ta.momentum.rsi(df["close"], window=14)

    # MACD
    df["macd"] = ta.trend.macd(df["close"])
    df["macd_signal"] = ta.trend.macd_signal(df["close"])

    # ADX
    df["adx"] = ta.trend.adx(
        df["high"],
        df["low"],
        df["close"],
        window=14
    )

    # ATR
    df["atr"] = ta.volatility.average_true_range(
        df["high"],
        df["low"],
        df["close"],
        window=14
    )

    # Bollinger Bands
    bb = ta.volatility.BollingerBands(
        close=df["close"],
        window=20,
        window_dev=2
    )

    df["bb_upper"] = bb.bollinger_hband()
    df["bb_lower"] = bb.bollinger_lband()
    df["bb_middle"] = bb.bollinger_mavg()

    # Average Volume
    df["volume_sma"] = df["volume"].rolling(20).mean()

    return df
