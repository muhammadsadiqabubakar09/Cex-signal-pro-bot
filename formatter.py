def format_signal(symbol, signal_data, risk_data):

    reasons = "\n".join(
        [f"✅ {r}" for r in signal_data["reasons"]]
    )

    message = f"""
{signal_data['signal']}

Coin: {symbol}

Confidence: {signal_data['score']}%

Entry:
{risk_data['entry']}

Stop Loss:
{risk_data['stop_loss']}

Take Profit

TP1: {risk_data['tp1']}
TP2: {risk_data['tp2']}
TP3: {risk_data['tp3']}

Risk / Reward:
{risk_data['rr']}

Reasons

{reasons}
"""

    return message.strip()
