import requests

PRIMARY_URL = "https://data-api.binance.vision/api/v3/ticker/24hr"
FALLBACK_URL = "https://api.binance.com/api/v3/ticker/24hr"


# ==========================================
# ALWAYS SCAN
# ==========================================

CORE_COINS = [
    "BTCUSDT",
    "ETHUSDT",
    "BNBUSDT",
    "SOLUSDT"
]


# ==========================================
# FAVORITES
# ==========================================

FAVORITE_COINS = [
    "SUIUSDT",
    "SEIUSDT",
    "NOTUSDT",
    "LINKUSDT",
    "ARBUSDT",
    "APTUSDT"
]


# ==========================================
# BLACKLIST
# ==========================================

BLACKLIST = {

    # Stablecoins
    "USDCUSDT",
    "FDUSDUSDT",
    "TUSDUSDT",
    "BUSDUSDT",

    # Fiat pairs
    "EURUSDT",
    "EURIUSDT",
    "AEURUSDT",
    "TRYUSDT",
    "BRLUSDT",
    "RUBUSDT",
    "UAHUSDT",
    "BIDRUSDT",

}


# Ignore leveraged tokens
IGNORE_SUFFIX = (
    "UPUSDT",
    "DOWNUSDT",
    "BULLUSDT",
    "BEARUSDT"
)


def download_market():

    for url in (
        PRIMARY_URL,
        FALLBACK_URL
    ):

        try:

            response = requests.get(
                url,
                timeout=10
            )

            response.raise_for_status()

            return response.json()

        except Exception:
            continue

    raise Exception(
        "Unable to fetch Binance market data."
    )


def is_good_coin(symbol):

    if not symbol.endswith("USDT"):
        return False

    if symbol in BLACKLIST:
        return False

    for suffix in IGNORE_SUFFIX:

        if symbol.endswith(suffix):
            return False

    return True


def get_watchlist(limit=35):

    data = download_market()

    usdt_pairs = []

    for coin in data:

        symbol = coin["symbol"]

        if not is_good_coin(symbol):
            continue

        try:

            volume = float(
                coin["quoteVolume"]
            )

            change = abs(
                float(
                    coin["priceChangePercent"]
                )
            )

        except Exception:
            continue

        # ===========================
        # QUALITY FILTER
        # ===========================

        if volume < 10_000_000:
            continue

        score = volume + (
            change * 2_000_000
        )

        usdt_pairs.append(
            (
                score,
                symbol
            )
        )

    usdt_pairs.sort(
        reverse=True
    )

    dynamic = []

    for _, symbol in usdt_pairs:

        if (
            symbol not in CORE_COINS
            and symbol not in FAVORITE_COINS
        ):

            dynamic.append(symbol)

        if len(dynamic) >= limit:
            break

    watchlist = (
        CORE_COINS
        + FAVORITE_COINS
        + dynamic
    )

    watchlist = list(
        dict.fromkeys(watchlist)
    )

    return watchlist