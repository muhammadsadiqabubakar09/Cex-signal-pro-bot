import os
import traceback

from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
)

from scanner import scan_market, auto_scan
from logger import log_info, log_error

TOKEN = os.getenv("BOT_TOKEN")

SCAN_INTERVAL = 300  # 5 minutes

# Store active chat IDs
ACTIVE_CHATS = set()


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    chat_id = update.effective_chat.id
    ACTIVE_CHATS.add(chat_id)

    await update.message.reply_text(
        "✅ CEX Signal Pro Bot is Online.\n\n"
        "🤖 Auto Scan: Every 5 Minutes\n"
        "📡 Auto signals are now enabled for this chat.\n\n"
        "Commands:\n"
        "/scan - Manual market scan"
    )

    log_info(f"Chat registered: {chat_id}")


async def scan(update: Update, context: ContextTypes.DEFAULT_TYPE):

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

        log_info(
            f"Manual scan completed. {len(results)} signal(s)."
        )

    except Exception:

        error = traceback.format_exc()

        log_error(error)

        await update.message.reply_text(
            f"<pre>{error}</pre>",
            parse_mode=ParseMode.HTML
        )


async def scheduled_scan(context: ContextTypes.DEFAULT_TYPE):

    try:

        results = auto_scan()

        if not results:
            return

        for chat_id in ACTIVE_CHATS:

            for message in results:

                try:

                    await context.bot.send_message(
                        chat_id=chat_id,
                        text=message,
                        parse_mode=ParseMode.HTML
                    )

                except Exception:

                    log_error(traceback.format_exc())

        log_info(
            f"Auto scan completed. {len(results)} signal(s)."
        )

    except Exception:

        log_error(traceback.format_exc())


def main():

    if not TOKEN:
        raise ValueError(
            "BOT_TOKEN environment variable is missing."
        )

    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("scan", scan))

    app.job_queue.run_repeating(
        scheduled_scan,
        interval=SCAN_INTERVAL,
        first=30
    )

    log_info("Bot started successfully.")

    app.run_polling()


if __name__ == "__main__":
    main()