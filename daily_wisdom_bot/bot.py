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
    begin_series_command,
    end_series_command,
    upcoming_series_command,
    view_series_command,
    get_next_series_command,
    start_up_callback,
    periodic_save_callback,
)
from job_utils import JobData, store_jobs, retrieve_jobs


async def start_command(update: Update, _: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        f"Hi, I'm {environ['BOT_USERNAME']} but you can call me Socrates!\n"
        + "I can help you set up a daily reading schedule of a book of your choice.\n"
        + "* Write `/view` to check the book series available\n"
        + "* Write `/begin <book> <HH:MM>` and I'll send you a daily a chapter at HH:MM to read. You can also write `/begin <book>` to begin series right away.\n"
        + "* Write `/end <book>` and I'll stop sending you messages for that book series\n"
        + "* Write `/upcoming` to see your scheduled messages\n"
        + "* Write `/next <book>` to get next part of book series ahead of schedule\n"
        "* Write `/help` to see these commands again\n" + "Happy reading :)"
    )


# Main function to run the bot
def main() -> None:
    """Run bot."""
    application = ApplicationBuilder().token(environ["BOT_TOKEN"]).build()

    application.job_queue.run_once(callback=start_up_callback, when=5)
    application.job_queue.run_repeating(
        callback=periodic_save_callback, interval=60, first=30
    )

    # Register the command handler with the dispatcher
    application.add_handler(CommandHandler(["start", "help"], start_command))
    application.add_handler(
        CommandHandler(["begin", "begin_series"], begin_series_command)
    )
    application.add_handler(CommandHandler(["end", "end_series"], end_series_command))
    application.add_handler(
        CommandHandler(["upcoming", "upcoming_series"], upcoming_series_command)
    )
    application.add_handler(
        CommandHandler(["view", "view_series"], view_series_command)
    )
    application.add_handler(CommandHandler(["next"], get_next_series_command))

    # Run the bot until the user presses Ctrl-C
    application.run_polling()
    # application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
