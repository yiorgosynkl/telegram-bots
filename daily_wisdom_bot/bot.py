import logging

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

from os import environ
from dotenv import load_dotenv

load_dotenv()

from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from book_commands import (
    start_series_command,
    stop_series_command,
    check_series_command,
)


async def start_command(update: Update, _: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "Hi! Use /set_message <seconds> to start reading a book daily. Use /unset_message to stop the book anytime!"
    )


# Main function to run the bot
def main() -> None:
    """Run bot."""
    application = ApplicationBuilder().token(environ["BOT_TOKEN"]).build()

    # Register the command handler with the dispatcher
    application.add_handler(CommandHandler(["start", "help"], start_command))
    application.add_handler(CommandHandler("start_series", start_series_command))
    application.add_handler(CommandHandler("stop_series", stop_series_command))
    application.add_handler(CommandHandler("check_series", check_series_command))

    # Run the bot until the user presses Ctrl-C
    application.run_polling()
    # application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
