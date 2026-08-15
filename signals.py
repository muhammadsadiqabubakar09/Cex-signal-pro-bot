from typing import Dict

============================================================

SIGNAL SCORE LIMITS

============================================================

ELITE_SCORE = 90
STRONG_SCORE = 80
VALID_SCORE = 70

============================================================

HELPERS

============================================================

def get_smc(tf_data: Dict) -> Dict:
"""
Safely return SMC data from a timeframe.
"""

return tf_data.get("smc", {}) or {}

def is_bullish_smc(tf_data: Dict) -> bool:
"""
Check whether SMC gives bullish confirmation.
"""

smc = get_smc(tf_data)  

bullish_items = 0  

if smc.get("structure") == "BULLISH":  
    bullish_items += 1  

if smc.get("bos") == "BULLISH":  
    bullish_items += 1  

if smc.get("choch") == "BULLISH":  
    bullish_items += 1  

if smc.get("liquidity_sweep") == "BULLISH":  
    bullish_items += 1  

fvg = smc.get("fvg", {})  
if fvg.get("type") == "BULLISH":  
    bullish_items += 1  

order_block = smc.get("order_block", {})  
if order_block.get("type") == "BULLISH":  
    bullish_items += 1  

return bullish_items >= 2

def is_bearish_smc(tf_data: Dict) -> bool:
"""
Check whether SMC gives bearish confirmation.
"""

smc = get_smc(tf_data)  

bearish_items = 0  

if smc.get("structure") == "BEARISH":  
    bearish_items += 1  

if smc.get("bos") == "BEARISH":  
    bearish_items += 1  

if smc.get("choch") == "BEARISH":  
    bearish_items += 1  

if smc.get("liquidity_sweep") == "BEARISH":  
    bearish_items += 1  

fvg = smc.get("fvg", {})  
if fvg.get("type") == "BEARISH":  
    bearish_items += 1  

order_block = smc.get("order_block", {})  
if order_block.get("type") == "BEARISH":  
    bearish_items += 1  

return bearish_items >= 2

============================================================

MAIN SIGNAL GENERATOR

============================================================

def generate_signal(mtf_data: Dict):
"""
Professional Multi-Timeframe Signal Generator.

Timeframe hierarchy:  

    1D  -> Macro trend  
    4H  -> Main trend  
    1H  -> Structure  
    15M -> Setup  
    5M  -> Entry confirmation  

Returns a signal dictionary compatible with  
risk_manager.py and formatter.py.  
"""  

score = 0  
reasons = []  

# ========================================================  
# SCORE BREAKDOWN  
# ========================================================  

trend_score = 0  
setup_score = 0  
entry_score = 0  
smc_score = 0  
momentum_score = 0  
confirmation_score = 0  

signal = "⚪ NO TRADE"  
market = "NONE"  
direction = "NONE"  
confidence = "LOW"  

# ========================================================  
# VALIDATION  
# ========================================================  

required_timeframes = [  
    "5m",  
    "15m",  
    "1h",  
    "4h",  
    "1d"  
]  

for timeframe in required_timeframes:  

    if timeframe not in mtf_data:  
        return {  
            "signal": signal,  
            "market": market,  
            "direction": direction,  
            "score": 0,  
            "confidence": confidence,  
            "reasons": ["Incomplete timeframe data"],  
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

# ========================================================  
# MACRO TREND — 1D  
# ========================================================  

daily_bullish = (  
    tf1d["ema20"] > tf1d["ema50"] > tf1d["ema200"]  
)  

daily_bearish = (  
    tf1d["ema20"] < tf1d["ema50"] < tf1d["ema200"]  
)  

# ========================================================  
# MAIN TREND — 4H + 1H  
# ========================================================  

bullish_4h = (  
    tf4h["ema20"] > tf4h["ema50"] > tf4h["ema200"]  
)  

bearish_4h = (  
    tf4h["ema20"] < tf4h["ema50"] < tf4h["ema200"]  
)  

bullish_1h = (  
    tf1h["ema20"] > tf1h["ema50"] > tf1h["ema200"]  
)  

bearish_1h = (  
    tf1h["ema20"] < tf1h["ema50"] < tf1h["ema200"]  
)  

# ========================================================  
# DETERMINE PRIMARY DIRECTION  
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
# TREND SCORE — 35 POINTS  
# ========================================================  

if bullish_trend:  

    score += 15  
    trend_score += 15  
    reasons.append("1D Bullish Macro Trend")  

    score += 10  
    trend_score += 10  
    reasons.append("4H Bullish Trend")  

    score += 10  
    trend_score += 10  
    reasons.append("1H Bullish Trend")  

elif bearish_trend:  

    score += 15  
    trend_score += 15  
    reasons.append("1D Bearish Macro Trend")  

    score += 10  
    trend_score += 10  
    reasons.append("4H Bearish Trend")  

    score += 10  
    trend_score += 10  
    reasons.append("1H Bearish Trend")  

# ========================================================  
# 15M SETUP — 8 POINTS  
# ========================================================  

bullish_15m = tf15["ema20"] > tf15["ema50"]  
bearish_15m = tf15["ema20"] < tf15["ema50"]  

if bullish_trend and bullish_15m:  

    score += 8  
    setup_score += 8  
    reasons.append("15M Bullish Setup")  

elif bearish_trend and bearish_15m:  

    score += 8  
    setup_score += 8  
    reasons.append("15M Bearish Setup")  

# ========================================================  
# 5M ENTRY TREND — 7 POINTS  
# ========================================================  

bullish_5m = tf5["ema20"] > tf5["ema50"]  
bearish_5m = tf5["ema20"] < tf5["ema50"]  

if bullish_trend and bullish_5m:  

    score += 7  
    entry_score += 7  
    reasons.append("5M Bullish Entry Trend")  

elif bearish_trend and bearish_5m:  

    score += 7  
    entry_score += 7  
    reasons.append("5M Bearish Entry Trend")  

# ========================================================  
# SMC — 20 POINTS  
# ========================================================  

if bullish_trend:  

    if is_bullish_smc(tf4h):  
        score += 5  
        smc_score += 5  
        reasons.append("4H Bullish SMC Confirmation")  

    if is_bullish_smc(tf1h):  
        score += 5  
        smc_score += 5  
        reasons.append("1H Bullish SMC Confirmation")  

    if is_bullish_smc(tf15):  
        score += 5  
        smc_score += 5  
        reasons.append("15M Bullish SMC Setup")  

    if is_bullish_smc(tf5):  
        score += 5  
        smc_score += 5  
        reasons.append("5M Bullish SMC Confirmation")  

elif bearish_trend:  

    if is_bearish_smc(tf4h):  
        score += 5  
        smc_score += 5  
        reasons.append("4H Bearish SMC Confirmation")  

    if is_bearish_smc(tf1h):  
        score += 5  
        smc_score += 5  
        reasons.append("1H Bearish SMC Confirmation")  

    if is_bearish_smc(tf15):  
        score += 5  
        smc_score += 5  
        reasons.append("15M Bearish SMC Setup")  

    if is_bearish_smc(tf5):  
        score += 5  
        smc_score += 5  
        reasons.append("5M Bearish SMC Confirmation")  

# ========================================================  
# MOMENTUM — 12 POINTS  
# ========================================================  

if bullish_trend:  

    if 50 <= tf5["rsi"] <= 70:  
        score += 4  
        momentum_score += 4  
        reasons.append("Healthy Bullish RSI")  

    if tf5["macd"] > tf5["macd_signal"]:  
        score += 4  
        momentum_score += 4  
        reasons.append("Bullish MACD")  

    if tf5["macd_hist"] > 0:  
        score += 2  
        momentum_score += 2  
        reasons.append("Positive MACD Histogram")  

    if tf5["stoch_rsi_k"] > tf5["stoch_rsi_d"]:  
        score += 2  
        momentum_score += 2  
        reasons.append("Bullish Stoch RSI")  

elif bearish_trend:  

    if 30 <= tf5["rsi"] <= 50:  
        score += 4  
        momentum_score += 4  
        reasons.append("Healthy Bearish RSI")  

    if tf5["macd"] < tf5["macd_signal"]:  
        score += 4  
        momentum_score += 4  
        reasons.append("Bearish MACD")  

    if tf5["macd_hist"] < 0:  
        score += 2  
        momentum_score += 2  
        reasons.append("Negative MACD Histogram")  

    if tf5["stoch_rsi_k"] < tf5["stoch_rsi_d"]:  
        score += 2  
        momentum_score += 2  
        reasons.append("Bearish Stoch RSI")  

# ========================================================  
# MARKET CONFIRMATION — 10 POINTS  
# ========================================================  

if tf5["adx"] >= 25:  

    score += 4  
    confirmation_score += 4  
    reasons.append("Strong ADX")  

if tf5["volume"] > tf5["volume_sma"]:  

    score += 3  
    confirmation_score += 3  
    reasons.append("Above Average Volume")  

if bullish_trend and tf5["close"] > tf5["vwap"]:  

    score += 3  
    confirmation_score += 3  
    reasons.append("Price Above VWAP")  

elif bearish_trend and tf5["close"] < tf5["vwap"]:  

    score += 3  
    confirmation_score += 3  
    reasons.append("Price Below VWAP")  

# ========================================================  
# FINAL SCORE CAP  
# ========================================================  

score = min(score, 100)  

# ========================================================  
# SCORE BREAKDOWN  
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
# FINAL DECISION — LONG  
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

    elif score >= VALID_SCORE:  

        signal = "🟢 BUY"  
        market = "SPOT"  
        direction = "BUY"  
        confidence = "MEDIUM"  

# ========================================================  
# FINAL DECISION — SHORT  
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

    elif score >= VALID_SCORE:  

        signal = "🔴 SELL"  
        market = "SPOT"  
        direction = "SELL"  
        confidence = "MEDIUM"  

# ========================================================  
# SAFETY FILTER  
# ========================================================  

if direction == "NONE":  

    return {  
        "signal": "⚪ NO TRADE",  
        "market": "NONE",  
        "direction": "NONE",  
        "score": score,  
        "confidence": "LOW",  
        "reasons": reasons,  
        "score_breakdown": score_breakdown  
    }  

# ========================================================  
# RETURN  
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