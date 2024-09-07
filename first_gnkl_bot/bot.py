import asyncio
import logging
from telegram import Update
from telegram import MessageEntity
from telegram.ext import (
    ApplicationBuilder,
    ContextTypes,
    CommandHandler,
    MessageHandler,
    filters,
)

from os import environ
from dotenv import load_dotenv

# import pdb

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

load_dotenv()


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=f"Hey, I'm {environ['BOT_USERNAME']}, a bot created by gnkl! I have different functionalities that you can use!",
    )


async def hellolater(update: Update, context: ContextTypes.DEFAULT_TYPE):
    def get_secs(args, default=10):
        try:
            return min(max(5, int(args[0])), 60)
        except:
            return default

    wait_secs = get_secs(context.args)
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=f"Hello, i'll text you again in {wait_secs} seconds!",
    )
    await asyncio.sleep(wait_secs)
    await context.bot.send_message(
        chat_id=update.effective_chat.id, text="Hello again :)"
    )


async def cap(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = " ".join(context.args).upper()
    text = text if text else "WRITE SOMETHING FOR ME TO CAPITALIZE"
    await context.bot.send_message(chat_id=update.effective_chat.id, text=text)


async def bold(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # docs: https://docs.python-telegram-bot.org/en/v21.5/telegram.messageentity.html
    text_list = update.effective_message.text.split()
    text = " ".join(text_list[1:])  # skip first word (the command)
    text = text if text else "write some text, I'll make it bold"
    entities = [MessageEntity(offset=0, length=len(text), type=MessageEntity.BOLD)]
    await context.bot.send_message(
        chat_id=update.effective_chat.id, text=text, entities=entities
    )


async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(
        chat_id=update.effective_chat.id, text=update.message.text
    )


if __name__ == "__main__":
    application = ApplicationBuilder().token(environ["BOT_TOKEN"]).build()

    start_handler = CommandHandler("start", start)
    application.add_handler(start_handler)
    cap_handler = CommandHandler("cap", cap)
    application.add_handler(cap_handler)
    bold_handler = CommandHandler("bold", bold)
    application.add_handler(bold_handler)
    hellolater_handler = CommandHandler("hellolater", hellolater)
    application.add_handler(hellolater_handler)
    echo_handler = MessageHandler(filters.TEXT & (~filters.COMMAND), echo)
    application.add_handler(echo_handler)

    application.run_polling()
