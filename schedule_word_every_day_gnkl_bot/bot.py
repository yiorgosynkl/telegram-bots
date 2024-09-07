import logging

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

from os import environ
from dotenv import load_dotenv

load_dotenv()

from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from timer_commands import set_timer_command, unset_timer_command
from schedule_commands import schedule_command, unschedule_command


async def start_command(update: Update, _: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "Hi! Use /set <seconds> to set a timer. Use /unset to stop the time!"
    )


# Main function to run the bot
def main() -> None:
    """Run bot."""
    application = ApplicationBuilder().token(environ["BOT_TOKEN"]).build()

    # Register the command handler with the dispatcher
    application.add_handler(CommandHandler(["start", "help"], start_command))
    application.add_handler(CommandHandler("set", set_timer_command))
    application.add_handler(CommandHandler("unset", unset_timer_command))
    application.add_handler(CommandHandler("schedule", schedule_command))
    application.add_handler(CommandHandler("unschedule", unschedule_command))

    # Run the bot until the user presses Ctrl-C
    application.run_polling()
    # application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
