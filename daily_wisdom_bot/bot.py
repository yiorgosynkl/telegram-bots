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
    view_series_command,
)


async def start_command(update: Update, _: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        f"Hi, I'm {environ['BOT_USERNAME']} but you can call me Socrates!\n"
        + "I can help you set up a daily reading schedule of a book of your choice.\n"
        + "* Write `/view_series` to check the books available\n"
        + "* Write `/start_series <book> <HH:MM>` and I'll send you a daily a chapter at HH:MM to read\n"
        + "* Write `/stop_series_command <book>` and I'll stop sending you messages for that book\n"
        + "* Write `/check_my_series <book>` to see the current schedule you have\n"
        "* Write `/help` to see these commands again\n" + "Happy reading :)"
    )


# Main function to run the bot
def main() -> None:
    """Run bot."""
    application = ApplicationBuilder().token(environ["BOT_TOKEN"]).build()

    # Register the command handler with the dispatcher
    application.add_handler(CommandHandler(["start", "help"], start_command))
    application.add_handler(CommandHandler("start_series", start_series_command))
    application.add_handler(CommandHandler("stop_series", stop_series_command))
    application.add_handler(CommandHandler("check_my_series", check_series_command))
    application.add_handler(CommandHandler("view_series", view_series_command))

    # Run the bot until the user presses Ctrl-C
    application.run_polling()
    # application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
