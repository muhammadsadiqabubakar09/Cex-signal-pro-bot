from datetime import datetime


def format_signal(symbol, signal_data, risk_data):
    """
    Format trading signal for Telegram.
    """

    if not risk_data:
        return None

    reasons = "\n".join(
        f"✅ {reason}" for reason in signal_data["reasons"]
    )

    timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")

    message = f"""
🚀 <b>CEX SIGNAL PRO</b>

🪙 <b>Coin:</b> {symbol}

📊 <b>Market:</b> {risk_data["market"]}
📈 <b>Direction:</b> {risk_data["direction"]}

⭐ <b>Confidence:</b> {signal_data["confidence"]}
🎯 <b>Score:</b> {signal_data["score"]}/100

━━━━━━━━━━━━━━━━━━

💰 <b>Entry:</b>
<code>{risk_data["entry"]}</code>

🛑 <b>Stop Loss:</b>
<code>{risk_data["stop_loss"]}</code>

🎯 <b>Take Profit</b>

TP1: <code>{risk_data["tp1"]}</code>
TP2: <code>{risk_data["tp2"]}</code>
TP3: <code>{risk_data["tp3"]}</code>

━━━━━━━━━━━━━━━━━━

⚖️ <b>Risk / Reward:</b>
{risk_data["risk_reward"]}

📉 <b>Risk:</b>
{risk_data["risk_percent"]}%

📈 <b>Reward:</b>
{risk_data["reward_percent"]}%

⚡ <b>Suggested Leverage:</b>
{risk_data["suggested_leverage"]}

━━━━━━━━━━━━━━━━━━

📌 <b>Reasons</b>

{reasons}

━━━━━━━━━━━━━━━━━━

🕒 <b>Generated:</b>
{timestamp}

⚠️ <i>Always use proper risk management. Never risk more than you can afford to lose.</i>
"""

    return message.strip()