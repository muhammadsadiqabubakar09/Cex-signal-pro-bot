import requests

PRIMARY_URL = "https://data-api.binance.vision/api/v3/ticker/24hr"
FALLBACK_URL = "https://api.binance.com/api/v3/ticker/24hr"

# Always scan these coins
CORE_COINS = [
    "BTCUSDT",
    "ETHUSDT",
    "BNBUSDT",
    "SOLUSDT"
]

# Your favorite coins
FAVORITE_COINS = [
    "SUIUSDT",
    "SEIUSDT",
    "NOTUSDT"
]

# Coins to ignore
BLACKLIST = [
    "USDCUSDT",
    "FDUSDUSDT",
    "TUSDUSDT",
    "BUSDUSDT"
]


def download_market():

    for url in (PRIMARY_URL, FALLBACK_URL):

        try:

            response = requests.get(url, timeout=10)
            response.raise_for_status()

            return response.json()

        except Exception:
            continue

    raise Exception("Unable to fetch Binance market data.")


def get_watchlist(limit=30):

    data = download_market()

    usdt_pairs = [
        coin for coin in data
        if coin["symbol"].endswith("USDT")
        and coin["symbol"] not in BLACKLIST
    ]

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

    watchlist = CORE_COINS + FAVORITE_COINS + dynamic

    return list(dict.fromkeys(watchlist))