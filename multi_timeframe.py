from binance_api import get_candles
from indicators import add_indicators

Multi-Timeframe Analysis

TIMEFRAMES = ["5m", "15m", "1h", "4h"]

def analyze_timeframe(symbol, interval):
"""
Analyze one timeframe and return all indicators.
"""

try:  
    df = get_candles(symbol, interval)  

    if df is None or df.empty:  
        return None  

    df = add_indicators(df)  

    if df is None or df.empty:  
        return None  

    last = df.iloc[-1]  

    return {  

        # Price  
        "close": last["close"],  

        # EMA  
        "ema20": last["ema20"],  
        "ema50": last["ema50"],  
        "ema200": last["ema200"],  

        # RSI  
        "rsi": last["rsi"],  

        # Stochastic RSI  
        "stoch_rsi": last["stoch_rsi"],  
        "stoch_rsi_k": last["stoch_rsi_k"],  
        "stoch_rsi_d": last["stoch_rsi_d"],  

        # MACD  
        "macd": last["macd"],  
        "macd_signal": last["macd_signal"],  
        "macd_hist": last["macd_hist"],  

        # ADX  
        "adx": last["adx"],  

        # ATR  
        "atr": last["atr"],  

        # Bollinger Bands  
        "bb_upper": last["bb_upper"],  
        "bb_middle": last["bb_middle"],  
        "bb_lower": last["bb_lower"],  
        "bb_width": last["bb_width"],  

        # VWAP  
        "vwap": last["vwap"],  

        # Volume  
        "volume": last["volume"],  
        "volume_sma": last["volume_sma"]  
    }  

except Exception:  
    return None

def analyze_symbol(symbol):
"""
Analyze all timeframes.
"""

result = {}  

for timeframe in TIMEFRAMES:  

    data = analyze_timeframe(symbol, timeframe)  

    if data is None:  
        return None  

    result[timeframe] = data  

return result