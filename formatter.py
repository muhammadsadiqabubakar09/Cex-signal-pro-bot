from datetime import datetime, timezone


# ============================================================
# TELEGRAM SIGNAL FORMATTER V2
# ============================================================

def format_signal(
    symbol,
    signal_data,
    risk_data
):
    """
    Format a validated trading signal for Telegram.

    IMPORTANT:
        This module does NOT calculate or modify
        Entry, Stop Loss or Take Profit.

        All trading calculations must come from
        risk_manager.py.
    """

    # ========================================================
    # BASIC VALIDATION
    # ========================================================

    if not isinstance(
        signal_data,
        dict
    ):
        return None

    if not isinstance(
        risk_data,
        dict
    ):
        return None

    # ========================================================
    # REQUIRED SIGNAL DATA
    # ========================================================

    required_signal_fields = [
        "signal",
        "direction",
        "market",
        "score",
        "confidence",
        "reasons"
    ]

    for field in required_signal_fields:

        if field not in signal_data:

            return None

    # ========================================================
    # REQUIRED RISK DATA
    # ========================================================

    required_risk_fields = [
        "market",
        "direction",
        "entry",
        "stop_loss",
        "tp1",
        "tp2",
        "tp3",
        "risk_percent",
        "reward_percent",
        "risk_reward",
        "suggested_leverage"
    ]

    for field in required_risk_fields:

        if field not in risk_data:

            return None

    # ========================================================
    # EXTRACT SIGNAL DATA
    # ========================================================

    signal = str(
        signal_data["signal"]
    )

    direction = str(
        risk_data["direction"]
    )

    market = str(
        risk_data["market"]
    )

    confidence = str(
        signal_data["confidence"]
    )

    score = signal_data["score"]

    # ========================================================
    # VALIDATE SCORE
    # ========================================================

    try:

        score = float(score)

    except (
        TypeError,
        ValueError
    ):

        return None

    if score < 0:

        return None

    # ========================================================
    # REASONS
    # ========================================================

    reasons_data = signal_data.get(
        "reasons",
        []
    )

    if not isinstance(
        reasons_data,
        list
    ):

        reasons_data = []

    valid_reasons = []

    for reason in reasons_data:

        if reason is None:

            continue

        reason = str(
            reason
        ).strip()

        if reason:

            valid_reasons.append(
                reason
            )

    if valid_reasons:

        reasons = "\n".join(
            f"✅ {reason}"
            for reason in valid_reasons
        )

    else:

        reasons = (
            "⚠️ No additional confirmation details."
        )

    # ========================================================
    # FORMAT NUMBERS
    # ========================================================

    def format_price(value):

        try:

            number = float(value)

        except (
            TypeError,
            ValueError
        ):

            return str(value)

        # ----------------------------------------------------
        # Preserve useful precision for low-priced coins
        # ----------------------------------------------------

        if number >= 1000:

            return f"{number:.2f}"

        if number >= 1:

            return f"{number:.6f}".rstrip(
                "0"
            ).rstrip(
                "."
            )

        if number >= 0.01:

            return f"{number:.8f}".rstrip(
                "0"
            ).rstrip(
                "."
            )

        return f"{number:.10f}".rstrip(
            "0"
        ).rstrip(
            "."
        )

    # ========================================================
    # PRICES
    # ========================================================

    entry = format_price(
        risk_data["entry"]
    )

    stop_loss = format_price(
        risk_data["stop_loss"]
    )

    tp1 = format_price(
        risk_data["tp1"]
    )

    tp2 = format_price(
        risk_data["tp2"]
    )

    tp3 = format_price(
        risk_data["tp3"]
    )

    # ========================================================
    # RISK INFORMATION
    # ========================================================

    try:

        risk_percent = float(
            risk_data["risk_percent"]
        )

        reward_percent = float(
            risk_data["reward_percent"]
        )

        risk_reward = float(
            risk_data["risk_reward"]
        )

    except (
        TypeError,
        ValueError
    ):

        return None

    leverage = str(
        risk_data["suggested_leverage"]
    )

    # ========================================================
    # SIGNAL TYPE
    # ========================================================

    if "ELITE" in signal:

        signal_label = "🔥 ELITE SETUP"

    elif "STRONG" in signal:

        signal_label = "💎 STRONG SETUP"

    elif direction in [
        "LONG",
        "BUY"
    ]:

        signal_label = "🟢 VALID LONG SETUP"

    elif direction == "SHORT":

        signal_label = "🔴 VALID SHORT SETUP"

    else:

        signal_label = signal

    # ========================================================
    # TIMESTAMP
    # ========================================================

    timestamp = datetime.now(
        timezone.utc
    ).strftime(
        "%Y-%m-%d %H:%M UTC"
    )

    # ========================================================
    # MARKET LABEL
    # ========================================================

    if market == "FUTURES":

        market_label = "⚡ FUTURES"

    elif market == "SPOT":

        market_label = "💰 SPOT"

    else:

        market_label = market

    # ========================================================
    # DIRECTION LABEL
    # ========================================================

    if direction in [
        "LONG",
        "BUY"
    ]:

        direction_label = "🟢 LONG"

    elif direction == "SHORT":

        direction_label = "🔴 SHORT"

    else:

        direction_label = direction

    # ========================================================
    # TELEGRAM MESSAGE
    # ========================================================

    message = f"""
🚀 <b>CEX SIGNAL PRO</b>

🪙 <b>COIN:</b> {symbol}

{market_label}
{direction_label}

⭐ <b>SETUP:</b> {signal_label}
🎯 <b>SCORE:</b> {score:.0f}/100
📊 <b>CONFIDENCE:</b> {confidence}

━━━━━━━━━━━━━━━━━━

💰 <b>ENTRY</b>

<code>{entry}</code>

🛑 <b>STOP LOSS</b>

<code>{stop_loss}</code>

━━━━━━━━━━━━━━━━━━

🎯 <b>TAKE PROFIT TARGETS</b>

TP1 → <code>{tp1}</code>
TP2 → <code>{tp2}</code>
TP3 → <code>{tp3}</code>

━━━━━━━━━━━━━━━━━━

⚖️ <b>RISK / REWARD</b>

R:R → <b>1:{risk_reward:.2f}</b>

📉 Risk → {risk_percent:.2f}%
📈 Reward → {reward_percent:.2f}%

⚡ Leverage → <b>{leverage}</b>

━━━━━━━━━━━━━━━━━━

📌 <b>SIGNAL CONFIRMATIONS</b>

{reasons}

━━━━━━━━━━━━━━━━━━

🕒 <b>Generated:</b>
{timestamp}

⚠️ <i>Signal confirmation does not guarantee a profitable trade.
Always use proper risk management.</i>
"""

    return message.strip()