import os


# ============================================================
# TELEGRAM CONFIGURATION
# ============================================================

BOT_TOKEN = os.getenv(
    "BOT_TOKEN"
)

CHAT_ID = os.getenv(
    "CHAT_ID"
)


# ============================================================
# MARKET CONFIGURATION
# ============================================================

SYMBOLS = [
    "BTCUSDT",
    "ETHUSDT",
    "SOLUSDT",
    "BNBUSDT"
]


# ============================================================
# DEFAULT TIMEFRAME
# ============================================================

TIMEFRAME = "15m"


# ============================================================
# VALIDATION
# ============================================================

if not BOT_TOKEN:

    raise RuntimeError(
        "BOT_TOKEN environment variable is not configured."
    )


if not CHAT_ID:

    raise RuntimeError(
        "CHAT_ID environment variable is not configured."
    )