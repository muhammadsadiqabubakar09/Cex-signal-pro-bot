def format_signal(symbol, signal_data, risk_data):

    reasons = "\n".join(
        [f"✅ {r}" for r in signal_data["reasons"]]
    )

    message = f"""
{signal_data['signal']}

Coin:
{symbol}

Market:
{signal_data['market']}

Direction:
{signal_data['direction']}

Confidence:
{signal_data['score']}% ({signal_data['confidence']})

Entry:
{risk_data['entry']}

Stop Loss:
{risk_data['stop_loss']}

Take Profit

TP1:
{risk_data['tp1']}

TP2:
{risk_data['tp2']}

TP3:
{risk_data['tp3']}

Risk:
{risk_data['risk_percent']}%

Reward:
{risk_data['reward_percent']}%

Risk / Reward:
1 : {risk_data['risk_reward']}

Suggested Leverage:
{risk_data['suggested_leverage']}

Reasons

{reasons}
"""

    return message.strip()