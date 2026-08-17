from typing import Dict


# ============================================================
# SIGNAL SCORE LIMITS
# ============================================================

ELITE_SCORE = 90
STRONG_SCORE = 80
VALID_SCORE = 75


# ============================================================
# MINIMUM CONFIRMATION REQUIREMENTS
# ============================================================

MIN_SMC_CONFIRMATIONS = 2

MIN_ADX = 20

MIN_RSI_BULLISH = 50
MAX_RSI_BULLISH = 70

MIN_RSI_BEARISH = 30
MAX_RSI_BEARISH = 50


# ============================================================
# HELPERS
# ============================================================

def get_smc(tf_data: Dict) -> Dict:
    """
    Safely return SMC data from a timeframe.
    """

    return tf_data.get(
        "smc",
        {}
    ) or {}


# ============================================================
# BULLISH SMC COUNT
# ============================================================

def bullish_smc_count(
    tf_data: Dict
) -> int:
    """
    Count bullish SMC confirmations.
    """

    smc = get_smc(
        tf_data
    )

    count = 0

    if smc.get("structure") == "BULLISH":
        count += 1

    if smc.get("bos") == "BULLISH":
        count += 1

    if smc.get("choch") == "BULLISH":
        count += 1

    if smc.get("liquidity_sweep") == "BULLISH":
        count += 1

    fvg = smc.get(
        "fvg",
        {}
    ) or {}

    if fvg.get("type") == "BULLISH":
        count += 1

    order_block = smc.get(
        "order_block",
        {}
    ) or {}

    if order_block.get("type") == "BULLISH":
        count += 1

    return count


# ============================================================
# BEARISH SMC COUNT
# ============================================================

def bearish_smc_count(
    tf_data: Dict
) -> int:
    """
    Count bearish SMC confirmations.
    """

    smc = get_smc(
        tf_data
    )

    count = 0

    if smc.get("structure") == "BEARISH":
        count += 1

    if smc.get("bos") == "BEARISH":
        count += 1

    if smc.get("choch") == "BEARISH":
        count += 1

    if smc.get("liquidity_sweep") == "BEARISH":
        count += 1

    fvg = smc.get(
        "fvg",
        {}
    ) or {}

    if fvg.get("type") == "BEARISH":
        count += 1

    order_block = smc.get(
        "order_block",
        {}
    ) or {}

    if order_block.get("type") == "BEARISH":
        count += 1

    return count


# ============================================================
# SMC DIRECTION
# ============================================================

def is_bullish_smc(
    tf_data: Dict
) -> bool:
    """
    Require minimum bullish SMC confirmation.
    """

    return (
        bullish_smc_count(
            tf_data
        )
        >= MIN_SMC_CONFIRMATIONS
    )


def is_bearish_smc(
    tf_data: Dict
) -> bool:
    """
    Require minimum bearish SMC confirmation.
    """

    return (
        bearish_smc_count(
            tf_data
        )
        >= MIN_SMC_CONFIRMATIONS
    )


# ============================================================
# EMPTY SIGNAL
# ============================================================

def no_trade(
    score=0,
    reasons=None,
    breakdown=None
):
    """
    Standard NO TRADE response.
    """

    return {
        "signal": "⚪ NO TRADE",
        "market": "NONE",
        "direction": "NONE",
        "score": score,
        "confidence": "LOW",
        "reasons": reasons or [],
        "score_breakdown": breakdown or {
            "trend": 0,
            "setup": 0,
            "entry": 0,
            "smc": 0,
            "momentum": 0,
            "confirmation": 0
        }
    }


# ============================================================
# VALIDATE TIMEFRAMES
# ============================================================

def validate_timeframes(
    mtf_data: Dict
):
    """
    Ensure every required timeframe exists.
    """

    required = [
        "5m",
        "15m",
        "1h",
        "4h",
        "1d"
    ]

    if not isinstance(
        mtf_data,
        dict
    ):
        return False

    for timeframe in required:

        if timeframe not in mtf_data:
            return False

        if not isinstance(
            mtf_data[timeframe],
            dict
        ):
            return False

    return True


# ============================================================
# MAIN SIGNAL GENERATOR
# ============================================================

def generate_signal(
    mtf_data: Dict
):
    """
    Strict professional multi-timeframe signal engine.

    Hierarchy:

        1D  = Macro direction
        4H  = Main trend
        1H  = Market structure
        15M = Setup
        5M  = Entry

    Score alone cannot create a signal.
    """

    # ========================================================
    # VALIDATION
    # ========================================================

    if not validate_timeframes(
        mtf_data
    ):

        return no_trade(
            reasons=[
                "Incomplete timeframe data"
            ]
        )

    tf5 = mtf_data["5m"]
    tf15 = mtf_data["15m"]
    tf1h = mtf_data["1h"]
    tf4h = mtf_data["4h"]
    tf1d = mtf_data["1d"]

    # ========================================================
    # SCORE VARIABLES
    # ========================================================

    score = 0

    reasons = []

    trend_score = 0
    setup_score = 0
    entry_score = 0
    smc_score = 0
    momentum_score = 0
    confirmation_score = 0

    # ========================================================
    # 1D MACRO TREND
    # ========================================================

    daily_bullish = (
        tf1d["ema20"]
        > tf1d["ema50"]
        > tf1d["ema200"]
    )

    daily_bearish = (
        tf1d["ema20"]
        < tf1d["ema50"]
        < tf1d["ema200"]
    )

    # ========================================================
    # 4H MAIN TREND
    # ========================================================

    bullish_4h = (
        tf4h["ema20"]
        > tf4h["ema50"]
        > tf4h["ema200"]
    )

    bearish_4h = (
        tf4h["ema20"]
        < tf4h["ema50"]
        < tf4h["ema200"]
    )

    # ========================================================
    # 1H STRUCTURE TREND
    # ========================================================

    bullish_1h = (
        tf1h["ema20"]
        > tf1h["ema50"]
        > tf1h["ema200"]
    )

    bearish_1h = (
        tf1h["ema20"]
        < tf1h["ema50"]
        < tf1h["ema200"]
    )

    # ========================================================
    # PRIMARY TREND ALIGNMENT
    # ========================================================

    bullish_trend = (
        daily_bullish
        and bullish_4h
        and bullish_1h
    )

    bearish_trend = (
        daily_bearish
        and bearish_4h
        and bearish_1h
    )

    # ========================================================
    # TREND SCORING
    # ========================================================

    if bullish_trend:

        score += 15
        trend_score += 15

        reasons.append(
            "1D Bullish Macro Trend"
        )

        score += 10
        trend_score += 10

        reasons.append(
            "4H Bullish Main Trend"
        )

        score += 10
        trend_score += 10

        reasons.append(
            "1H Bullish Structure Trend"
        )

    elif bearish_trend:

        score += 15
        trend_score += 15

        reasons.append(
            "1D Bearish Macro Trend"
        )

        score += 10
        trend_score += 10

        reasons.append(
            "4H Bearish Main Trend"
        )

        score += 10
        trend_score += 10

        reasons.append(
            "1H Bearish Structure Trend"
        )

    else:

        return no_trade(
            reasons=[
                "Higher timeframe trend is not aligned"
            ]
        )

    # ========================================================
    # 1H SMC STRUCTURE
    # ========================================================

    if bullish_trend:

        if not is_bullish_smc(
            tf1h
        ):

            return no_trade(
                score=score,
                reasons=reasons + [
                    "1H bullish SMC confirmation missing"
                ],
                breakdown={
                    "trend": trend_score,
                    "setup": setup_score,
                    "entry": entry_score,
                    "smc": smc_score,
                    "momentum": momentum_score,
                    "confirmation": confirmation_score
                }
            )

        score += 7
        smc_score += 7

        reasons.append(
            "1H Bullish SMC Structure Confirmed"
        )

    elif bearish_trend:

        if not is_bearish_smc(
            tf1h
        ):

            return no_trade(
                score=score,
                reasons=reasons + [
                    "1H bearish SMC confirmation missing"
                ],
                breakdown={
                    "trend": trend_score,
                    "setup": setup_score,
                    "entry": entry_score,
                    "smc": smc_score,
                    "momentum": momentum_score,
                    "confirmation": confirmation_score
                }
            )

        score += 7
        smc_score += 7

        reasons.append(
            "1H Bearish SMC Structure Confirmed"
        )

    # ========================================================
    # 15M SETUP
    # ========================================================

    bullish_15m = (
        tf15["ema20"]
        > tf15["ema50"]
    )

    bearish_15m = (
        tf15["ema20"]
        < tf15["ema50"]
    )

    if bullish_trend:

        if not bullish_15m:

            return no_trade(
                score=score,
                reasons=reasons + [
                    "15M bullish setup missing"
                ],
                breakdown={
                    "trend": trend_score,
                    "setup": setup_score,
                    "entry": entry_score,
                    "smc": smc_score,
                    "momentum": momentum_score,
                    "confirmation": confirmation_score
                }
            )

        score += 8
        setup_score += 8

        reasons.append(
            "15M Bullish Setup"
        )

        if is_bullish_smc(
            tf15
        ):

            score += 5
            smc_score += 5

            reasons.append(
                "15M Bullish SMC Setup"
            )

        else:

            return no_trade(
                score=score,
                reasons=reasons + [
                    "15M bullish SMC confirmation missing"
                ],
                breakdown={
                    "trend": trend_score,
                    "setup": setup_score,
                    "entry": entry_score,
                    "smc": smc_score,
                    "momentum": momentum_score,
                    "confirmation": confirmation_score
                }
            )

    elif bearish_trend:

        if not bearish_15m:

            return no_trade(
                score=score,
                reasons=reasons + [
                    "15M bearish setup missing"
                ],
                breakdown={
                    "trend": trend_score,
                    "setup": setup_score,
                    "entry": entry_score,
                    "smc": smc_score,
                    "momentum": momentum_score,
                    "confirmation": confirmation_score
                }
            )

        score += 8
        setup_score += 8

        reasons.append(
            "15M Bearish Setup"
        )

        if is_bearish_smc(
            tf15
        ):

            score += 5
            smc_score += 5

            reasons.append(
                "15M Bearish SMC Setup"
            )

        else:

            return no_trade(
                score=score,
                reasons=reasons + [
                    "15M bearish SMC confirmation missing"
                ],
                breakdown={
                    "trend": trend_score,
                    "setup": setup_score,
                    "entry": entry_score,
                    "smc": smc_score,
                    "momentum": momentum_score,
                    "confirmation": confirmation_score
                }
            )    # ========================================================
    # 5M ENTRY CONFIRMATION
    # ========================================================

    bullish_5m = (
        tf5["ema20"]
        > tf5["ema50"]
    )

    bearish_5m = (
        tf5["ema20"]
        < tf5["ema50"]
    )

    if bullish_trend:

        if not bullish_5m:

            return no_trade(
                score=score,
                reasons=reasons + [
                    "5M bullish entry trend missing"
                ],
                breakdown={
                    "trend": trend_score,
                    "setup": setup_score,
                    "entry": entry_score,
                    "smc": smc_score,
                    "momentum": momentum_score,
                    "confirmation": confirmation_score
                }
            )

        score += 7
        entry_score += 7

        reasons.append(
            "5M Bullish Entry Trend"
        )

        # ----------------------------------------------------
        # 5M SMC ENTRY CONFIRMATION
        # ----------------------------------------------------

        if not is_bullish_smc(tf5):

            return no_trade(
                score=score,
                reasons=reasons + [
                    "5M bullish SMC entry confirmation missing"
                ],
                breakdown={
                    "trend": trend_score,
                    "setup": setup_score,
                    "entry": entry_score,
                    "smc": smc_score,
                    "momentum": momentum_score,
                    "confirmation": confirmation_score
                }
            )

        score += 5
        smc_score += 5

        reasons.append(
            "5M Bullish SMC Entry Confirmed"
        )

    elif bearish_trend:

        if not bearish_5m:

            return no_trade(
                score=score,
                reasons=reasons + [
                    "5M bearish entry trend missing"
                ],
                breakdown={
                    "trend": trend_score,
                    "setup": setup_score,
                    "entry": entry_score,
                    "smc": smc_score,
                    "momentum": momentum_score,
                    "confirmation": confirmation_score
                }
            )

        score += 7
        entry_score += 7

        reasons.append(
            "5M Bearish Entry Trend"
        )

        # ----------------------------------------------------
        # 5M SMC ENTRY CONFIRMATION
        # ----------------------------------------------------

        if not is_bearish_smc(tf5):

            return no_trade(
                score=score,
                reasons=reasons + [
                    "5M bearish SMC entry confirmation missing"
                ],
                breakdown={
                    "trend": trend_score,
                    "setup": setup_score,
                    "entry": entry_score,
                    "smc": smc_score,
                    "momentum": momentum_score,
                    "confirmation": confirmation_score
                }
            )

        score += 5
        smc_score += 5

        reasons.append(
            "5M Bearish SMC Entry Confirmed"
        )

    # ========================================================
    # MOMENTUM CONFIRMATION
    # ========================================================

    if bullish_trend:

        # ----------------------------------------------------
        # RSI
        # ----------------------------------------------------

        if not (
            MIN_RSI_BULLISH
            <= tf5["rsi"]
            <= MAX_RSI_BULLISH
        ):

            return no_trade(
                score=score,
                reasons=reasons + [
                    "5M bullish RSI confirmation missing"
                ],
                breakdown={
                    "trend": trend_score,
                    "setup": setup_score,
                    "entry": entry_score,
                    "smc": smc_score,
                    "momentum": momentum_score,
                    "confirmation": confirmation_score
                }
            )

        score += 4
        momentum_score += 4

        reasons.append(
            "Healthy Bullish RSI"
        )

        # ----------------------------------------------------
        # MACD
        # ----------------------------------------------------

        if not (
            tf5["macd"]
            > tf5["macd_signal"]
        ):

            return no_trade(
                score=score,
                reasons=reasons + [
                    "Bullish MACD confirmation missing"
                ],
                breakdown={
                    "trend": trend_score,
                    "setup": setup_score,
                    "entry": entry_score,
                    "smc": smc_score,
                    "momentum": momentum_score,
                    "confirmation": confirmation_score
                }
            )

        score += 4
        momentum_score += 4

        reasons.append(
            "Bullish MACD"
        )

        # ----------------------------------------------------
        # MACD HISTOGRAM
        # ----------------------------------------------------

        if tf5["macd_hist"] <= 0:

            return no_trade(
                score=score,
                reasons=reasons + [
                    "Positive MACD histogram missing"
                ],
                breakdown={
                    "trend": trend_score,
                    "setup": setup_score,
                    "entry": entry_score,
                    "smc": smc_score,
                    "momentum": momentum_score,
                    "confirmation": confirmation_score
                }
            )

        score += 2
        momentum_score += 2

        reasons.append(
            "Positive MACD Histogram"
        )

        # ----------------------------------------------------
        # STOCH RSI
        # ----------------------------------------------------

        if not (
            tf5["stoch_rsi_k"]
            > tf5["stoch_rsi_d"]
        ):

            return no_trade(
                score=score,
                reasons=reasons + [
                    "Bullish Stoch RSI confirmation missing"
                ],
                breakdown={
                    "trend": trend_score,
                    "setup": setup_score,
                    "entry": entry_score,
                    "smc": smc_score,
                    "momentum": momentum_score,
                    "confirmation": confirmation_score
                }
            )

        score += 2
        momentum_score += 2

        reasons.append(
            "Bullish Stoch RSI"
        )

    elif bearish_trend:

        # ----------------------------------------------------
        # RSI
        # ----------------------------------------------------

        if not (
            MIN_RSI_BEARISH
            <= tf5["rsi"]
            <= MAX_RSI_BEARISH
        ):

            return no_trade(
                score=score,
                reasons=reasons + [
                    "5M bearish RSI confirmation missing"
                ],
                breakdown={
                    "trend": trend_score,
                    "setup": setup_score,
                    "entry": entry_score,
                    "smc": smc_score,
                    "momentum": momentum_score,
                    "confirmation": confirmation_score
                }
            )

        score += 4
        momentum_score += 4

        reasons.append(
            "Healthy Bearish RSI"
        )

        # ----------------------------------------------------
        # MACD
        # ----------------------------------------------------

        if not (
            tf5["macd"]
            < tf5["macd_signal"]
        ):

            return no_trade(
                score=score,
                reasons=reasons + [
                    "Bearish MACD confirmation missing"
                ],
                breakdown={
                    "trend": trend_score,
                    "setup": setup_score,
                    "entry": entry_score,
                    "smc": smc_score,
                    "momentum": momentum_score,
                    "confirmation": confirmation_score
                }
            )

        score += 4
        momentum_score += 4

        reasons.append(
            "Bearish MACD"
        )

        # ----------------------------------------------------
        # MACD HISTOGRAM
        # ----------------------------------------------------

        if tf5["macd_hist"] >= 0:

            return no_trade(
                score=score,
                reasons=reasons + [
                    "Negative MACD histogram missing"
                ],
                breakdown={
                    "trend": trend_score,
                    "setup": setup_score,
                    "entry": entry_score,
                    "smc": smc_score,
                    "momentum": momentum_score,
                    "confirmation": confirmation_score
                }
            )

        score += 2
        momentum_score += 2

        reasons.append(
            "Negative MACD Histogram"
        )

        # ----------------------------------------------------
        # STOCH RSI
        # ----------------------------------------------------

        if not (
            tf5["stoch_rsi_k"]
            < tf5["stoch_rsi_d"]
        ):

            return no_trade(
                score=score,
                reasons=reasons + [
                    "Bearish Stoch RSI confirmation missing"
                ],
                breakdown={
                    "trend": trend_score,
                    "setup": setup_score,
                    "entry": entry_score,
                    "smc": smc_score,
                    "momentum": momentum_score,
                    "confirmation": confirmation_score
                }
            )

        score += 2
        momentum_score += 2

        reasons.append(
            "Bearish Stoch RSI"
        )

    # ========================================================
    # MARKET CONFIRMATION
    # ========================================================

    # --------------------------------------------------------
    # ADX
    # --------------------------------------------------------

    if tf5["adx"] < MIN_ADX:

        return no_trade(
            score=score,
            reasons=reasons + [
                "Market trend strength is too weak"
            ],
            breakdown={
                "trend": trend_score,
                "setup": setup_score,
                "entry": entry_score,
                "smc": smc_score,
                "momentum": momentum_score,
                "confirmation": confirmation_score
            }
        )

    score += 4
    confirmation_score += 4

    reasons.append(
        "Acceptable ADX Trend Strength"
    )

    # --------------------------------------------------------
    # VOLUME
    # --------------------------------------------------------

    if tf5["volume"] <= tf5["volume_sma"]:

        return no_trade(
            score=score,
            reasons=reasons + [
                "Volume confirmation missing"
            ],
            breakdown={
                "trend": trend_score,
                "setup": setup_score,
                "entry": entry_score,
                "smc": smc_score,
                "momentum": momentum_score,
                "confirmation": confirmation_score
            }
        )

    score += 3
    confirmation_score += 3

    reasons.append(
        "Above Average Volume"
    )

    # --------------------------------------------------------
    # VWAP
    # --------------------------------------------------------

    if bullish_trend:

        if tf5["close"] <= tf5["vwap"]:

            return no_trade(
                score=score,
                reasons=reasons + [
                    "Price is not above VWAP"
                ],
                breakdown={
                    "trend": trend_score,
                    "setup": setup_score,
                    "entry": entry_score,
                    "smc": smc_score,
                    "momentum": momentum_score,
                    "confirmation": confirmation_score
                }
            )

        score += 3
        confirmation_score += 3

        reasons.append(
            "Price Above VWAP"
        )

    elif bearish_trend:

        if tf5["close"] >= tf5["vwap"]:

            return no_trade(
                score=score,
                reasons=reasons + [
                    "Price is not below VWAP"
                ],
                breakdown={
                    "trend": trend_score,
                    "setup": setup_score,
                    "entry": entry_score,
                    "smc": smc_score,
                    "momentum": momentum_score,
                    "confirmation": confirmation_score
                }
            )

        score += 3
        confirmation_score += 3

        reasons.append(
            "Price Below VWAP"
        )

    # ========================================================
    # FINAL SCORE
    # ========================================================

    score = min(
        int(score),
        100
    )

    # ========================================================
    # FINAL BREAKDOWN
    # ========================================================

    score_breakdown = {
        "trend": trend_score,
        "setup": setup_score,
        "entry": entry_score,
        "smc": smc_score,
        "momentum": momentum_score,
        "confirmation": confirmation_score
    }

    # ========================================================
    # FINAL SCORE THRESHOLD
    # ========================================================

    if score < VALID_SCORE:

        return no_trade(
            score=score,
            reasons=reasons + [
                "Final score below valid signal threshold"
            ],
            breakdown=score_breakdown
        )

    # ========================================================
    # BULLISH FINAL DECISION
    # ========================================================

    if bullish_trend:

        if score >= ELITE_SCORE:

            signal = "🔥 ELITE LONG"
            market = "FUTURES"
            direction = "LONG"
            confidence = "VERY HIGH"

        elif score >= STRONG_SCORE:

            signal = "🟢 STRONG LONG"
            market = "FUTURES"
            direction = "LONG"
            confidence = "HIGH"

        else:

            signal = "🟢 BUY"
            market = "SPOT"
            direction = "BUY"
            confidence = "MEDIUM"

    # ========================================================
    # BEARISH FINAL DECISION
    # ========================================================

    elif bearish_trend:

        if score >= ELITE_SCORE:

            signal = "🔥 ELITE SHORT"
            market = "FUTURES"
            direction = "SHORT"
            confidence = "VERY HIGH"

        elif score >= STRONG_SCORE:

            signal = "🔴 STRONG SHORT"
            market = "FUTURES"
            direction = "SHORT"
            confidence = "HIGH"

        else:

            signal = "🔴 SELL"
            market = "SPOT"
            direction = "SELL"
            confidence = "MEDIUM"

    else:

        return no_trade(
            score=score,
            reasons=reasons,
            breakdown=score_breakdown
        )

    # ========================================================
    # FINAL SAFETY VALIDATION
    # ========================================================

    if direction == "NONE":

        return no_trade(
            score=score,
            reasons=reasons,
            breakdown=score_breakdown
        )

    # ========================================================
    # RETURN FINAL SIGNAL
    # ========================================================

    return {
        "signal": signal,
        "market": market,
        "direction": direction,
        "score": score,
        "confidence": confidence,
        "reasons": reasons,
        "score_breakdown": score_breakdown
    }