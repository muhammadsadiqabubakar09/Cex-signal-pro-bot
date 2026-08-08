import ta


def add_indicators(df):
    """
    Add technical indicators to the market dataframe.
    """

    # ==========================
    # EMA
    # ==========================
    df["ema20"] = ta.trend.ema_indicator(df["close"], window=20)
    df["ema50"] = ta.trend.ema_indicator(df["close"], window=50)
    df["ema200"] = ta.trend.ema_indicator(df["close"], window=200)

    # ==========================
    # RSI
    # ==========================
    df["rsi"] = ta.momentum.rsi(df["close"], window=14)

    # ==========================
    # Stochastic RSI
    # ==========================
    stoch = ta.momentum.StochRSIIndicator(
        close=df["close"],
        window=14,
        smooth1=3,
        smooth2=3
    )

    df["stoch_rsi"] = stoch.stochrsi()
    df["stoch_rsi_k"] = stoch.stochrsi_k()
    df["stoch_rsi_d"] = stoch.stochrsi_d()

    # ==========================
    # MACD
    # ==========================
    df["macd"] = ta.trend.macd(df["close"])
    df["macd_signal"] = ta.trend.macd_signal(df["close"])
    df["macd_hist"] = ta.trend.macd_diff(df["close"])

    # ==========================
    # ADX
    # ==========================
    df["adx"] = ta.trend.adx(
        df["high"],
        df["low"],
        df["close"],
        window=14
    )

    # ==========================
    # ATR
    # ==========================
    df["atr"] = ta.volatility.average_true_range(
        df["high"],
        df["low"],
        df["close"],
        window=14
    )

    # ==========================
    # Bollinger Bands
    # ==========================
    bb = ta.volatility.BollingerBands(
        close=df["close"],
        window=20,
        window_dev=2
    )

    df["bb_upper"] = bb.bollinger_hband()
    df["bb_middle"] = bb.bollinger_mavg()
    df["bb_lower"] = bb.bollinger_lband()
    df["bb_width"] = bb.bollinger_wband()

    # ==========================
    # VWAP
    # ==========================
    try:
        df["vwap"] = ta.volume.volume_weighted_average_price(
            high=df["high"],
            low=df["low"],
            close=df["close"],
            volume=df["volume"]
        )
    except Exception:
        # Fallback idan ta library bata goyi bayan wannan function ba
        df["vwap"] = (
            (df["close"] * df["volume"]).cumsum()
            / df["volume"].cumsum()
        )

    # ==========================
    # Average Volume
    # ==========================
    df["volume_sma"] = df["volume"].rolling(window=20).mean()

    # ==========================
    # Clean Data
    # ==========================
    df = df.dropna().reset_index(drop=True)

    return df