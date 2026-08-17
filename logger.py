import logging
import os


# ============================================================
# LOGGING CONFIGURATION
# ============================================================

LOG_DIR = "logs"
LOG_FILE = os.path.join(
    LOG_DIR,
    "bot.log"
)


# ============================================================
# CREATE LOG DIRECTORY
# ============================================================

try:

    os.makedirs(
        LOG_DIR,
        exist_ok=True
    )

except Exception:
    # Railway/container environment should still
    # be able to continue with console logging.
    pass


# ============================================================
# HANDLERS
# ============================================================

handlers = [
    logging.StreamHandler()
]


# ============================================================
# FILE HANDLER
# ============================================================

try:

    file_handler = logging.FileHandler(
        LOG_FILE,
        encoding="utf-8"
    )

    handlers.append(
        file_handler
    )

except Exception:
    # If file logging is unavailable,
    # console logging remains active.
    pass


# ============================================================
# LOGGING CONFIGURATION
# ============================================================

logging.basicConfig(
    level=logging.INFO,
    format=(
        "%(asctime)s | "
        "%(levelname)s | "
        "%(message)s"
    ),
    handlers=handlers
)


# ============================================================
# LOGGER
# ============================================================

logger = logging.getLogger(
    "CEXSignalPro"
)


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def log_info(message):
    """
    Log an informational message.
    """

    logger.info(
        str(message)
    )


def log_warning(message):
    """
    Log a warning message.
    """

    logger.warning(
        str(message)
    )


def log_error(message):
    """
    Log an error message.
    """

    logger.error(
        str(message)
    )