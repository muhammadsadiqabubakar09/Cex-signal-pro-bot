from typing import Dict


# ============================================================
# SIGNAL ENGINE — V2
# ============================================================

MIN_SCORE = 75

ELITE_SCORE = 90
STRONG_SCORE = 82

REQUIRED_TIMEFRAMES = [
    "5m",
    "15m",
    "1h",
    "4h",
    "1d"
]


# ============================================================
# HELPERS
# ============================================================

def get_smc(tf_data: Dict) -> Dict:
    return tf_data.get(
        "smc",
        {}
    ) or {}


def get_fvg(tf_data: Dict) -> Dict:
    smc = get_smc(tf_data)

    return smc.get(
        "fvg",
        {}
    ) or {}


def get_order_block(tf_data: Dict) -> Dict:
    smc = get_smc(tf_data)

    return smc.get(
        "order_block",
        {}
    ) or {}


def get_structure(tf_data: Dict):
    smc = get_smc(tf_data)

    return smc.get(
        "structure"
    )


def get_bos(tf_data: Dict):
    smc = get_smc(tf_data)

    return smc.get(
        "bos"
    )


def get_choch(tf_data: Dict):
    smc = get_smc(tf_data)

    return smc.get(
        "choch"
    )


def get_liquidity_sweep(tf_data: Dict):
    smc = get_smc(tf_data)

    return smc.get(
        "liquidity_sweep"
    )


def get_displacement(tf_data: Dict):
    smc = get_smc(tf_data)

    return smc.get(
        "displacement"
    )


# ============================================================
# TIMEFRAME VALIDATION
# ============================================================

def validate_timeframes(mtf_data: Dict):

    if not isinstance(
        mtf_data,
        dict
    ):

        return False

    for timeframe in REQUIRED_TIMEFRAMES:

        if timeframe not in mtf_data:

            return False

        if not isinstance(
            mtf_data[timeframe],
            dict
        ):

            return False

    return True


# ============================================================
# TREND DETECTION
# ============================================================

def detect_trend(tf_data: Dict):

    try:

        ema20 = float(
            tf_data["ema20"]
        )

        ema50 = float(
            tf_data["ema50"]
        )

        ema200 = float(
            tf_data["ema200"]
        )

    except Exception:

        return "NEUTRAL"

    if (
        ema20 > ema50
        and ema50 > ema200
    ):

        return "BULLISH"

    if (
        ema20 < ema50
        and ema50 < ema200
    ):

        return "BEARISH"

    return "NEUTRAL"


# ============================================================
# MACRO BIAS
# ============================================================

def detect_macro_bias(tf1d: Dict):

    return detect_trend(
        tf1d
    )


# ============================================================
# PRIMARY TREND
# ============================================================

def detect_primary_trend(
    tf4h: Dict,
    tf1h: Dict
):

    trend_4h = detect_trend(
        tf4h
    )

    trend_1h = detect_trend(
        tf1h
    )

    if (
        trend_4h == "BULLISH"
        and trend_1h == "BULLISH"
    ):

        return "BULLISH"

    if (
        trend_4h == "BEARISH"
        and trend_1h == "BEARISH"
    ):

        return "BEARISH"

    return "NEUTRAL"


# ============================================================
# STRUCTURE CONFIRMATION
# ============================================================

def structure_confirmation(
    tf1h: Dict,
    direction: str
):

    structure = get_structure(
        tf1h
    )

    bos = get_bos(
        tf1h
    )

    choch = get_choch(
        tf1h
    )

    if direction == "LONG":

        if structure == "BULLISH":
            return True

        if bos == "BULLISH":
            return True

        if choch == "BULLISH":
            return True

    elif direction == "SHORT":

        if structure == "BEARISH":
            return True

        if bos == "BEARISH":
            return True

        if choch == "BEARISH":
            return True

    return False


# ============================================================
# 15M SETUP
# ============================================================

def setup_confirmation(
    tf15: Dict,
    direction: str
):

    trend = detect_trend(
        tf15
    )

    if direction == "LONG":

        if trend != "BULLISH":
            return False

        smc = get_smc(
            tf15
        )

        confirmations = sum([
            smc.get("structure") == "BULLISH",
            smc.get("bos") == "BULLISH",
            smc.get("choch") == "BULLISH",
            smc.get("liquidity_sweep") == "BULLISH",
            get_fvg(tf15).get("type") == "BULLISH",
            get_order_block(tf15).get("type") == "BULLISH",
            get_displacement(tf15) == "BULLISH"
        ])

        return confirmations >= 2

    if direction == "SHORT":

        if trend != "BEARISH":
            return False

        smc = get_smc(
            tf15
        )

        confirmations = sum([
            smc.get("structure") == "BEARISH",
            smc.get("bos") == "BEARISH",
            smc.get("choch") == "BEARISH",
            smc.get("liquidity_sweep") == "BEARISH",
            get_fvg(tf15).get("type") == "BEARISH",
            get_order_block(tf15).get("type") == "BEARISH",
            get_displacement(tf15) == "BEARISH"
        ])

        return confirmations >= 2

    return False


# ============================================================
# 5M ENTRY CONFIRMATION
# ============================================================

def entry_confirmation(
    tf5: Dict,
    direction: str
):

    try:

        ema20 = float(
            tf5["ema20"]
        )

        ema50 = float(
            tf5["ema50"]
        )

        rsi = float(
            tf5["rsi"]
        )

        macd = float(
            tf5["macd"]
        )

        macd_signal = float(
            tf5["macd_signal"]
        )

        stoch_k = float(
            tf5["stoch_rsi_k"]
        )

        stoch_d = float(
            tf5["stoch_rsi_d"]
        )

        close = float(
            tf5["close"]
        )

        vwap = float(
            tf5["vwap"]
        )

        adx = float(
            tf5["adx"]
        )

    except Exception:

        return False

    # --------------------------------------------------------
    # LONG
    # --------------------------------------------------------

    if direction == "LONG":

        confirmations = 0

        if ema20 > ema50:
            confirmations += 1

        if 50 <= rsi <= 68:
            confirmations += 1

        if macd > macd_signal:
            confirmations += 1

        if stoch_k > stoch_d:
            confirmations += 1

        if close > vwap:
            confirmations += 1

        if adx >= 20:
            confirmations += 1

        return confirmations >= 4

    # --------------------------------------------------------
    # SHORT
    # --------------------------------------------------------

    if direction == "SHORT":

        confirmations = 0

        if ema20 < ema50:
            confirmations += 1

        if 32 <= rsi <= 50:
            confirmations += 1

        if macd < macd_signal:
            confirmations += 1

        if stoch_k < stoch_d:
            confirmations += 1

        if close < vwap:
            confirmations += 1

        if adx >= 20:
            confirmations += 1

        return confirmations >= 4

    return False


# ============================================================
# SMC CONFIRMATION
# ============================================================

def smc_confirmation(
    tf4h: Dict,
    tf1h: Dict,
    tf15: Dict,
    tf5: Dict,
    direction: str
):

    timeframes = [
        ("4H", tf4h),
        ("1H", tf1h),
        ("15M", tf15),
        ("5M", tf5)
    ]

    confirmations = 0
    reasons = []

    for name, tf_data in timeframes:

        structure = get_structure(
            tf_data
        )

        bos = get_bos(
            tf_data
        )

        choch = get_choch(
            tf_data
        )

        sweep = get_liquidity_sweep(
            tf_data
        )

        fvg = get_fvg(
            tf_data
        )

        order_block = get_order_block(
            tf_data
        )

        if direction == "LONG":

            if structure == "BULLISH":
                confirmations += 1
                reasons.append(
                    f"{name} Bullish Structure"
                )

            if bos == "BULLISH":
                confirmations += 1
                reasons.append(
                    f"{name} Bullish BOS"
                )

            if choch == "BULLISH":
                confirmations += 1
                reasons.append(
                    f"{name} Bullish CHOCH"
                )

            if sweep == "BULLISH":
                confirmations += 1
                reasons.append(
                    f"{name} Bullish Liquidity Sweep"
                )

            if fvg.get("type") == "BULLISH":
                confirmations += 1
                reasons.append(
                    f"{name} Bullish FVG"
                )

            if order_block.get("type") == "BULLISH":
                confirmations += 1
                reasons.append(
                    f"{name} Bullish Order Block"
                )

        elif direction == "SHORT":

            if structure == "BEARISH":
                confirmations += 1
                reasons.append(
                    f"{name} Bearish Structure"
                )

            if bos == "BEARISH":
                confirmations += 1
                reasons.append(
                    f"{name} Bearish BOS"
                )

            if choch == "BEARISH":
                confirmations += 1
                reasons.append(
                    f"{name} Bearish CHOCH"
                )

            if sweep == "BEARISH":
                confirmations += 1
                reasons.append(
                    f"{name} Bearish Liquidity Sweep"
                )

            if fvg.get("type") == "BEARISH":
                confirmations += 1
                reasons.append(
                    f"{name} Bearish FVG"
                )

            if order_block.get("type") == "BEARISH":
                confirmations += 1
                reasons.append(
                    f"{name} Bearish Order Block"
                )

    # --------------------------------------------------------
    # Require genuine multi-timeframe confirmation
    # --------------------------------------------------------

    return (
        confirmations >= 4,
        confirmations,
        reasons
    )


# ============================================================
# MOMENTUM CONFIRMATION
# ============================================================

def momentum_confirmation(
    tf5: Dict,
    direction: str
):

    try:

        rsi = float(
            tf5["rsi"]
        )

        macd = float(
            tf5["macd"]
        )

        macd_signal = float(
            tf5["macd_signal"]
        )

        macd_hist = float(
            tf5["macd_hist"]
        )

        stoch_k = float(
            tf5["stoch_rsi_k"]
        )

        stoch_d = float(
            tf5["stoch_rsi_d"]
        )

    except Exception:

        return False, 0, []

    score = 0
    reasons = []

    if direction == "LONG":

        if 50 <= rsi <= 68:
            score += 2
            reasons.append(
                "Healthy Bullish RSI"
            )

        if macd > macd_signal:
            score += 2
            reasons.append(
                "Bullish MACD"
            )

        if macd_hist > 0:
            score += 1
            reasons.append(
                "Positive MACD Histogram"
            )

        if stoch_k > stoch_d:
            score += 1
            reasons.append(
                "Bullish Stoch RSI"
            )

        return (
            score >= 3,
            score,
            reasons
        )

    if direction == "SHORT":

        if 32 <= rsi <= 50:
            score += 2
            reasons.append(
                "Healthy Bearish RSI"
            )

        if macd < macd_signal:
            score += 2
            reasons.append(
                "Bearish MACD"
            )

        if macd_hist < 0:
            score += 1
            reasons.append(
                "Negative MACD Histogram"
            )

        if stoch_k < stoch_d:
            score += 1
            reasons.append(
                "Bearish Stoch RSI"
            )

        return (
            score >= 3,
            score,
            reasons
        )

    return False, 0, []


# ============================================================
# MARKET CONFIRMATION
# ============================================================

def market_confirmation(
    tf5: Dict,
    direction: str
):

    try:

        adx = float(
            tf5["adx"]
        )

        volume = float(
            tf5["volume"]
        )

        volume_sma = float(
            tf5["volume_sma"]
        )

        close = float(
            tf5["close"]
        )

        vwap = float(
            tf5["vwap"]
        )

    except Exception:

        return False, 0, []

    score = 0
    reasons = []

    # --------------------------------------------------------
    # ADX
    # --------------------------------------------------------

    if adx >= 25:

        score += 2

        reasons.append(
            "Strong ADX"
        )

    elif adx >= 20:

        score += 1

        reasons.append(
            "Developing Trend Strength"
        )

    # --------------------------------------------------------
    # Volume
    # --------------------------------------------------------

    if volume > volume_sma:

        score += 2

        reasons.append(
            "Above Average Volume"
        )

    # --------------------------------------------------------
    # VWAP
    # --------------------------------------------------------

    if direction == "LONG":

        if close > vwap:

            score += 1

            reasons.append(
                "Price Above VWAP"
            )

    elif direction == "SHORT":

        if close < vwap:

            score += 1

            reasons.append(
                "Price Below VWAP"
            )

    return (
        score >= 2,
        score,
        reasons
    )


# ============================================================
# FINAL SIGNAL GENERATOR
# ============================================================

def generate_signal(
    mtf_data: Dict
):

    # ========================================================
    # VALIDATE INPUT
    # ========================================================

    if not validate_timeframes(
        mtf_data
    ):

        return {
            "signal": "⚪ NO TRADE",
            "market": "NONE",
            "direction": "NONE",
            "score": 0,
            "confidence": "LOW",
            "reasons": [
                "Incomplete timeframe data"
            ],
            "score_breakdown": {
                "trend": 0,
                "setup": 0,
                "entry": 0,
                "smc": 0,
                "momentum": 0,
                "confirmation": 0
            }
        }

    tf5 = mtf_data["5m"]
    tf15 = mtf_data["15m"]
    tf1h = mtf_data["1h"]
    tf4h = mtf_data["4h"]
    tf1d = mtf_data["1d"]

    reasons = []

    # ========================================================
    # DETERMINE MARKET BIAS
    # ========================================================

    macro_bias = detect_macro_bias(
        tf1d
    )

    primary_trend = detect_primary_trend(
        tf4h,
        tf1h
    )

    # --------------------------------------------------------
    # Do not trade against the daily macro trend
    # --------------------------------------------------------

    if macro_bias == "BULLISH":

        if primary_trend != "BULLISH":

            return {
                "signal": "⚪ NO TRADE",
                "market": "NONE",
                "direction": "NONE",
                "score": 0,
                "confidence": "LOW",
                "reasons": [
                    "Daily bullish bias but 4H/1H trend is not aligned"
                ],
                "score_breakdown": {
                    "trend": 0,
                    "setup": 0,
                    "entry": 0,
                    "smc": 0,
                    "momentum": 0,
                    "confirmation": 0
                }
            }

        direction = "LONG"

    elif macro_bias == "BEARISH":

        if primary_trend != "BEARISH":

            return {
                "signal": "⚪ NO TRADE",
                "market": "NONE",
                "direction": "NONE",
                "score": 0,
                "confidence": "LOW",
                "reasons": [
                    "Daily bearish bias but 4H/1H trend is not aligned"
                ],
                "score_breakdown": {
                    "trend": 0,
                    "setup": 0,
                    "entry": 0,
                    "smc": 0,
                    "momentum": 0,
                    "confirmation": 0
                }
            }

        direction = "SHORT"

    else:

        return {
            "signal": "⚪ NO TRADE",
            "market": "NONE",
            "direction": "NONE",
            "score": 0,
            "confidence": "LOW",
            "reasons": [
                "Daily macro trend is neutral"
            ],
            "score_breakdown": {
                "trend": 0,
                "setup": 0,
                "entry": 0,
                "smc": 0,
                "momentum": 0,
                "confirmation": 0
            }
        }

    # ========================================================
    # SCORE BREAKDOWN
    # ========================================================

    trend_score = 0
    setup_score = 0
    entry_score = 0
    smc_score = 0
    momentum_score = 0
    confirmation_score = 0

    # ========================================================
    # TREND SCORE
    # ========================================================

    trend_score += 15

    reasons.append(
        f"1D {macro_bias} Macro Trend"
    )

    trend_score += 10

    reasons.append(
        f"4H {primary_trend} Main Trend"
    )

    trend_score += 10

    reasons.append(
        f"1H {primary_trend} Structure Trend"
    )

    # ========================================================
    # 15M SETUP
    # ========================================================

    setup_ok = setup_confirmation(
        tf15,
        direction
    )

    if not setup_ok:

        return {
            "signal": "⚪ NO TRADE",
            "market": "NONE",
            "direction": "NONE",
            "score": trend_score,
            "confidence": "LOW",
            "reasons": reasons + [
                "15M setup confirmation failed"
            ],
            "score_breakdown": {
                "trend": trend_score,
                "setup": 0,
                "entry": 0,
                "smc": 0,
                "momentum": 0,
                "confirmation": 0
            }
        }

    setup_score = 10

    reasons.append(
        "15M Valid SMC Setup"
    )

    # ========================================================
    # 5M ENTRY
    # ========================================================

    entry_ok = entry_confirmation(
        tf5,
        direction
    )

    if not entry_ok:

        return {
            "signal": "⚪ NO TRADE",
            "market": "NONE",
            "direction": "NONE",
            "score": trend_score + setup_score,
            "confidence": "LOW",
            "reasons": reasons + [
                "5M entry confirmation failed"
            ],
            "score_breakdown": {
                "trend": trend_score,
                "setup": setup_score,
                "entry": 0,
                "smc": 0,
                "momentum": 0,
                "confirmation": 0
            }
        }

    entry_score = 10

    reasons.append(
        "5M Entry Confirmation"
    )

    # ========================================================
    # SMC
    # ========================================================

    smc_ok, smc_count, smc_reasons = smc_confirmation(
        tf4h,
        tf1h,
        tf15,
        tf5,
        direction
    )

    if not smc_ok:

        return {
            "signal": "⚪ NO TRADE",
            "market": "NONE",
            "direction": "NONE",
            "score": trend_score + setup_score + entry_score,
            "confidence": "LOW",
            "reasons": reasons + [
                "Insufficient multi-timeframe SMC confirmation"
            ],
            "score_breakdown": {
                "trend": trend_score,
                "setup": setup_score,
                "entry": entry_score,
                "smc": 0,
                "momentum": 0,
                "confirmation": 0
            }
        }

    smc_score = min(
        15,
        smc_count * 2
    )

    reasons.extend(
        smc_reasons
    )

    # ========================================================
    # MOMENTUM
    # ========================================================

    momentum_ok, momentum_score, momentum_reasons = momentum_confirmation(
        tf5,
        direction
    )

    if not momentum_ok:

        return {
            "signal": "⚪ NO TRADE",
            "market": "NONE",
            "direction": "NONE",
            "score": (
                trend_score
                + setup_score
                + entry_score
                + smc_score
            ),
            "confidence": "LOW",
            "reasons": reasons + [
                "Momentum confirmation failed"
            ],
            "score_breakdown": {
                "trend": trend_score,
                "setup": setup_score,
                "entry": entry_score,
                "smc": smc_score,
                "momentum": momentum_score,
                "confirmation": 0
            }
        }

    reasons.extend(
        momentum_reasons
    )

    # ========================================================
    # MARKET CONFIRMATION
    # ========================================================

    confirmation_ok, confirmation_score, confirmation_reasons = market_confirmation(
        tf5,
        direction
    )

    if not confirmation_ok:

        return {
            "signal": "⚪ NO TRADE",
            "market": "NONE",
            "direction": "NONE",
            "score": (
                trend_score
                + setup_score
                + entry_score
                + smc_score
                + momentum_score
            ),
            "confidence": "LOW",
            "reasons": reasons + [
                "Market confirmation failed"
            ],
            "score_breakdown": {
                "trend": trend_score,
                "setup": setup_score,
                "entry": entry_score,
                "smc": smc_score,
                "momentum": momentum_score,
                "confirmation": confirmation_score
            }
        }

    reasons.extend(
        confirmation_reasons
    )

    # ========================================================
    # FINAL SCORE
    # ========================================================

    score = (
        trend_score
        + setup_score
        + entry_score
        + smc_score
        + momentum_score
        + confirmation_score
    )

    score = min(
        score,
        100
    )

    # ========================================================
    # FINAL DECISION
    # ========================================================

    if score < MIN_SCORE:

        return {
            "signal": "⚪ NO TRADE",
            "market": "NONE",
            "direction": "NONE",
            "score": score,
            "confidence": "LOW",
            "reasons": reasons + [
                f"Score below minimum threshold ({MIN_SCORE})"
            ],
            "score_breakdown": {
                "trend": trend_score,
                "setup": setup_score,
                "entry": entry_score,
                "smc": smc_score,
                "momentum": momentum_score,
                "confirmation": confirmation_score
            }
        }

    # ========================================================
    # LONG
    # ========================================================

    if direction == "LONG":

        if score >= ELITE_SCORE:

            signal = "🔥 ELITE LONG"
            market = "FUTURES"
            confidence = "VERY HIGH"

        elif score >= STRONG_SCORE:

            signal = "🟢 STRONG LONG"
            market = "FUTURES"
            confidence = "HIGH"

        else:

            signal = "🟢 LONG"
            market = "SPOT"
            confidence = "MEDIUM"

    # ========================================================
    # SHORT
    # ========================================================

    else:

        if score >= ELITE_SCORE:

            signal = "🔥 ELITE SHORT"
            market = "FUTURES"
            confidence = "VERY HIGH"

        elif score >= STRONG_SCORE:

            signal = "🔴 STRONG SHORT"
            market = "FUTURES"
            confidence = "HIGH"

        else:

            signal = "🔴 SHORT"
            market = "SPOT"
            confidence = "MEDIUM"

    # ========================================================
    # FINAL RETURN
    # ========================================================

    return {
        "signal": signal,
        "market": market,
        "direction": direction,
        "score": score,
        "confidence": confidence,
        "reasons": reasons,
        "score_breakdown": {
            "trend": trend_score,
            "setup": setup_score,
            "entry": entry_score,
            "smc": smc_score,
            "momentum": momentum_score,
            "confirmation": confirmation_score
        }
    }