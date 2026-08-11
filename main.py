import os

from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
)

from scanner import scan_market
from logger import log_info, log_error

TOKEN = os.getenv("BOT_TOKEN")


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Start command.
    """

    await update.message.reply_text(
        "✅ CEX Signal Pro Bot is Online.\n\n"
        "Available Commands:\n"
        "/scan - Scan market for trading signals"
    )


async def scan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Scan market and send signals.
    """

    await update.message.reply_text(
        "🔍 Scanning market...\nPlease wait..."
    )

    try:

        results = scan_market()

        if not results:
            await update.message.reply_text(
                "⚪ No high-quality trading signals found."
            )
            return

        for message in results:

            await update.message.reply_text(
                text=message,
                parse_mode=ParseMode.HTML
            )

        log_info(f"Market scan completed. {len(results)} signal(s) sent.")

    except Exception as e:

    import traceback

    error = traceback.format_exc()

    log_error(error)

    await update.message.reply_text(
        f"<pre>{error}</pre>",
        parse_mode=ParseMode.HTML
    )


def main():

    if not TOKEN:
        raise ValueError("BOT_TOKEN environment variable is missing.")

    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("scan", scan))

    log_info("Bot started successfully.")

    app.run_polling()


if __name__ == "__main__":
    main()