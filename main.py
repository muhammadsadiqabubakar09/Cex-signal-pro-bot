import os

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes
)

from scanner import scan_market
from logger import log_info, log_error

TOKEN = os.getenv("BOT_TOKEN", "")


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    await update.message.reply_text(
        "✅ CEX Signal Pro Bot is Online.\n\n"
        "Commands:\n"
        "/scan - Scan market for Top Signals"
    )


async def scan(update: Update, context: ContextTypes.DEFAULT_TYPE):

    await update.message.reply_text(
        "🔍 Scanning market...\nPlease wait..."
    )

    try:

        results = scan_market()

        if not results:

            await update.message.reply_text(
                "⚪ No high-quality trading signal found."
            )

            return

        for item in results:

            await update.message.reply_text(
                item["message"]
            )

        log_info("Market scan completed.")

    except Exception as e:

        log_error(str(e))

        await update.message.reply_text(
            "❌ Scan failed."
        )


def main():

    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("scan", scan))

    app.run_polling()


if __name__ == "__main__":
    main()