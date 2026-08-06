import requests

BINANCE_TICKER = "https://api.binance.com/api/v3/ticker/24hr"

# Waɗannan za su kasance koyaushe ana dubansu
CORE_COINS = [
    "BTCUSDT",
    "ETHUSDT",
    "BNBUSDT",
    "SOLUSDT"
]

# Coins da kai ka fi son a riƙa dubawa
FAVORITE_COINS = [
    "SUIUSDT",
    "SEIUSDT",
    "NOTUSDT"
]

# Coins da ba ma son scanner ya bincika
BLACKLIST = [
    "USDCUSDT",
    "FDUSDUSDT",
    "TUSDUSDT",
    "BUSDUSDT"
]


def get_watchlist(limit=30):

    response = requests.get(BINANCE_TICKER, timeout=10)
    response.raise_for_status()

    data = response.json()

    # USDT pairs kawai
    usdt_pairs = [
        coin for coin in data
        if coin["symbol"].endswith("USDT")
        and coin["symbol"] not in BLACKLIST
    ]

    # Sort by Quote Volume
    usdt_pairs.sort(
        key=lambda x: float(x["quoteVolume"]),
        reverse=True
    )

    dynamic = []

    for coin in usdt_pairs:

        symbol = coin["symbol"]

        if (
            symbol not in CORE_COINS
            and symbol not in FAVORITE_COINS
        ):
            dynamic.append(symbol)

        if len(dynamic) >= limit:
            break

    watchlist = []

    watchlist.extend(CORE_COINS)
    watchlist.extend(FAVORITE_COINS)
    watchlist.extend(dynamic)

    # Cire duplicates
    watchlist = list(dict.fromkeys(watchlist))

    return watchlist
