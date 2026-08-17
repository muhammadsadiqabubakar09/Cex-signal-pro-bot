import requests


# ============================================================
# BINANCE MARKET DATA
# ============================================================

PRIMARY_URL = "https://data-api.binance.vision/api/v3/ticker/24hr"
FALLBACK_URL = "https://api.binance.com/api/v3/ticker/24hr"

REQUEST_TIMEOUT = 10


# ============================================================
# CORE COINS
# ============================================================

CORE_COINS = [
    "BTCUSDT",
    "ETHUSDT",
    "BNBUSDT",
    "SOLUSDT"
]


# ============================================================
# FAVORITE COINS
# ============================================================

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
# LEVERAGED TOKEN FILTER
# ============================================================

IGNORE_SUFFIXES = (
    "UPUSDT",
    "DOWNUSDT",
    "BULLUSDT",
    "BEARUSDT"
)


# ============================================================
# WATCHLIST LIMITS
# ============================================================

MAX_DYNAMIC_COINS = 15

MIN_QUOTE_VOLUME = 10_000_000

MIN_PRICE_CHANGE = 1.5


# ============================================================
# DOWNLOAD 24H MARKET DATA
# ============================================================

def download_market():
    """
    Download Binance 24-hour ticker data.

    Uses a primary endpoint and automatically falls back
    to the secondary Binance endpoint if necessary.
    """

    for url in (
        PRIMARY_URL,
        FALLBACK_URL
    ):

        try:

            response = requests.get(
                url,
                timeout=REQUEST_TIMEOUT
            )

            response.raise_for_status()

            data = response.json()

            if (
                isinstance(data, list)
                and data
            ):
                return data

        except Exception:
            continue

    raise RuntimeError(
        "Unable to fetch Binance market data."
    )


# ============================================================
# SYMBOL VALIDATION
# ============================================================

def is_good_coin(symbol):
    """
    Reject symbols that are unsuitable for the scanner.
    """

    if not symbol:
        return False

    symbol = str(symbol).upper()

    if not symbol.endswith("USDT"):
        return False

    if symbol in BLACKLIST:
        return False

    for suffix in IGNORE_SUFFIXES:

        if symbol.endswith(suffix):
            return False

    return True


# ============================================================
# COIN QUALITY SCORE
# ============================================================

def calculate_coin_score(
    volume,
    price_change
):
    """
    Calculate a simple liquidity/activity score.

    Volume receives the larger weight because liquidity
    is more important than raw 24h price movement.

    This is NOT a market-cap ranking.
    """

    volume_score = min(
        volume / 10_000_000,
        100
    )

    volatility_score = min(
        price_change * 5,
        50
    )

    return (
        volume_score * 0.70
        + volatility_score * 0.30
    )


# ============================================================
# BUILD DYNAMIC WATCHLIST
# ============================================================

def get_dynamic_coins(
    data,
    limit=MAX_DYNAMIC_COINS
):
    """
    Select additional liquid and active USDT pairs.

    Core and favorite coins are excluded here because
    they are added separately.
    """

    candidates = []

    for coin in data:

        symbol = coin.get("symbol")

        if not is_good_coin(symbol):
            continue

        if symbol in CORE_COINS:
            continue

        if symbol in FAVORITE_COINS:
            continue

        try:

            volume = float(
                coin.get(
                    "quoteVolume",
                    0
                )
            )

            price_change = abs(
                float(
                    coin.get(
                        "priceChangePercent",
                        0
                    )
                )
            )

        except (
            TypeError,
            ValueError
        ):

            continue

        # ----------------------------------------------------
        # LIQUIDITY FILTER
        # ----------------------------------------------------

        if volume < MIN_QUOTE_VOLUME:
            continue

        # ----------------------------------------------------
        # ACTIVITY FILTER
        # ----------------------------------------------------

        if price_change < MIN_PRICE_CHANGE:
            continue

        score = calculate_coin_score(
            volume,
            price_change
        )

        candidates.append(
            {
                "symbol": symbol,
                "score": score,
                "volume": volume,
                "price_change": price_change
            }
        )

    # --------------------------------------------------------
    # HIGHEST QUALITY FIRST
    # --------------------------------------------------------

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

def get_watchlist(
    limit=MAX_DYNAMIC_COINS
):
    """
    Return the final scanner watchlist.

    Priority:

        1. Core coins
        2. Favorite coins
        3. Dynamic liquid coins

    Duplicates are automatically removed.
    """

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

    # --------------------------------------------------------
    # REMOVE DUPLICATES
    # --------------------------------------------------------

    watchlist = list(
        dict.fromkeys(watchlist)
    )

    return watchlist