import requests


# ============================================================
# BINANCE MARKET DATA
# ============================================================

PRIMARY_URL = "https://data-api.binance.vision/api/v3/ticker/24hr"
FALLBACK_URL = "https://api.binance.com/api/v3/ticker/24hr"


# ============================================================
# WATCHLIST CONFIGURATION
# ============================================================

CORE_COINS = [
    "BTCUSDT",
    "ETHUSDT",
    "BNBUSDT",
    "SOLUSDT"
]


FAVORITE_COINS = [
    "SUIUSDT",
    "SEIUSDT",
    "NOTUSDT",
    "LINKUSDT",
    "ARBUSDT",
    "APTUSDT"
]


# ============================================================
# BLACKLIST
# ============================================================

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


# ============================================================
# LEVERAGED TOKENS
# ============================================================

IGNORE_SUFFIX = (
    "UPUSDT",
    "DOWNUSDT",
    "BULLUSDT",
    "BEARUSDT"
)


# ============================================================
# FILTER SETTINGS
# ============================================================

MIN_QUOTE_VOLUME = 5_000_000

MIN_PRICE_CHANGE = 1.0

MAX_DYNAMIC_COINS = 35


# ============================================================
# DOWNLOAD MARKET DATA
# ============================================================

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

            data = response.json()

            if isinstance(data, list) and data:
                return data

        except Exception:
            continue

    raise Exception(
        "Unable to fetch Binance market data."
    )


# ============================================================
# BASIC COIN FILTER
# ============================================================

def is_good_coin(symbol):

    if not symbol.endswith("USDT"):
        return False

    if symbol in BLACKLIST:
        return False

    for suffix in IGNORE_SUFFIX:

        if symbol.endswith(suffix):
            return False

    return True


# ============================================================
# COIN QUALITY SCORE
# ============================================================

def calculate_coin_score(volume, change):

    """
    Rank coins using:
        - Trading volume
        - Volatility

    NOTE:
    Binance 24hr ticker does not provide market cap.
    Therefore this is NOT an actual market-cap ranking.
    """

    volume_score = min(
        volume / 10_000_000,
        100
    )

    volatility_score = min(
        change * 5,
        50
    )

    return (
        volume_score * 0.70
        + volatility_score * 0.30
    )


# ============================================================
# BUILD DYNAMIC WATCHLIST
# ============================================================

def get_dynamic_coins(data, limit=MAX_DYNAMIC_COINS):

    candidates = []

    for coin in data:

        symbol = coin.get("symbol")

        if not symbol:
            continue

        if not is_good_coin(symbol):
            continue

        # Do not duplicate core/favorite coins
        if symbol in CORE_COINS:
            continue

        if symbol in FAVORITE_COINS:
            continue

        try:

            volume = float(
                coin.get("quoteVolume", 0)
            )

            change = abs(
                float(
                    coin.get(
                        "priceChangePercent",
                        0
                    )
                )
            )

        except (TypeError, ValueError):

            continue

        # ====================================================
        # LIQUIDITY FILTER
        # ====================================================

        if volume < MIN_QUOTE_VOLUME:
            continue

        # ====================================================
        # ACTIVITY FILTER
        # ====================================================

        if change < MIN_PRICE_CHANGE:
            continue

        score = calculate_coin_score(
            volume,
            change
        )

        candidates.append(
            {
                "symbol": symbol,
                "score": score,
                "volume": volume,
                "change": change
            }
        )

    # Highest quality first
    candidates.sort(
        key=lambda item: item["score"],
        reverse=True
    )

    return [
        item["symbol"]
        for item in candidates[:limit]
    ]


# ============================================================
# FINAL WATCHLIST
# ============================================================

def get_watchlist(limit=MAX_DYNAMIC_COINS):

    data = download_market()

    dynamic_coins = get_dynamic_coins(
        data,
        limit=limit
    )

    watchlist = (
        CORE_COINS
        + FAVORITE_COINS
        + dynamic_coins
    )

    # Remove duplicates while preserving order
    watchlist = list(
        dict.fromkeys(watchlist)
    )

    return watchlist