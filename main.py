import time
import traceback

from telegram import Bot

from config import BOT_TOKEN
from scanner import auto_scan
from logger import log_info, log_error


# ============================================================
# AUTO-SCAN CONFIGURATION
# ============================================================

SCAN_INTERVAL = 5 * 60

STARTUP_DELAY = 10


# ============================================================
# TELEGRAM BOT
# ============================================================

bot = Bot(
    token=BOT_TOKEN
)


# ============================================================
# SEND SIGNAL
# ============================================================

def send_signal(message):
    """
    Send one validated signal message to Telegram.

    The actual destination/chat ID must be configured
    separately in config.py.
    """

    try:

        from config import CHAT_ID

    except ImportError:

        log_error(
            "CHAT_ID was not found in config.py"
        )

        return False

    if not CHAT_ID:

        log_error(
            "CHAT_ID is empty."
        )

        return False

    try:

        bot.send_message(
            chat_id=CHAT_ID,
            text=message,
            parse_mode="HTML"
        )

        return True

    except Exception:

        log_error(
            "Failed to send Telegram signal\n"
            + traceback.format_exc()
        )

        return False


# ============================================================
# PROCESS SCAN RESULTS
# ============================================================

def process_scan_results(results):
    """
    Send every newly generated signal to Telegram.
    """

    if not results:

        log_info(
            "No new valid signals found."
        )

        return

    sent = 0

    for message in results:

        if not message:

            continue

        if send_signal(message):

            sent += 1

    log_info(
        f"Telegram delivery completed | "
        f"Sent={sent} | "
        f"Generated={len(results)}"
    )


# ============================================================
# RUN ONE SCAN
# ============================================================

def run_scan():
    """
    Execute one complete market scan.
    """

    try:

        log_info(
            "========================================"
        )

        log_info(
            "Starting automatic market scan..."
        )

        start_time = time.time()

        results = auto_scan()

        if results is None:

            results = []

        process_scan_results(
            results
        )

        elapsed = (
            time.time()
            - start_time
        )

        log_info(
            f"Scan finished in "
            f"{elapsed:.2f} seconds"
        )

        log_info(
            "========================================"
        )

    except Exception:

        log_error(
            "Unexpected scan failure\n"
            + traceback.format_exc()
        )


# ============================================================
# MAIN AUTO-SCAN LOOP
# ============================================================

def main():
    """
    Main bot controller.

    The bot continuously scans the market every
    SCAN_INTERVAL seconds.

    A scan failure does NOT terminate the bot.
    """

    log_info(
        "========================================"
    )

    log_info(
        "CEX SIGNAL PRO V2.0 STARTING"
    )

    log_info(
        f"Auto-scan interval: "
        f"{SCAN_INTERVAL // 60} minutes"
    )

    log_info(
        f"Startup delay: "
        f"{STARTUP_DELAY} seconds"
    )

    log_info(
        "========================================"
    )

    # --------------------------------------------------------
    # Startup delay
    # --------------------------------------------------------

    time.sleep(
        STARTUP_DELAY
    )

    # --------------------------------------------------------
    # Continuous scanner
    # --------------------------------------------------------

    while True:

        scan_start = time.time()

        run_scan()

        # ----------------------------------------------------
        # Calculate remaining interval
        # ----------------------------------------------------

        elapsed = (
            time.time()
            - scan_start
        )

        remaining = (
            SCAN_INTERVAL
            - elapsed
        )

        if remaining < 0:

            remaining = 0

        log_info(
            f"Next scan in "
            f"{remaining:.0f} seconds"
        )

        try:

            time.sleep(
                remaining
            )

        except KeyboardInterrupt:

            log_info(
                "Scanner stopped manually."
            )

            break


# ============================================================
# APPLICATION ENTRY POINT
# ============================================================

if __name__ == "__main__":

    try:

        main()

    except KeyboardInterrupt:

        log_info(
            "CEX SIGNAL PRO stopped."
        )

    except Exception:

        log_error(
            "Fatal application error\n"
            + traceback.format_exc()
        )