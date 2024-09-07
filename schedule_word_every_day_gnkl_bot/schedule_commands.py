#!/usr/bin/env python

from datetime import datetime, time, timedelta
from telegram import Update
from telegram.ext import ContextTypes

async def schedule_callback(context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send the alarm message."""
    job = context.job
    await context.bot.send_message(job.chat_id, text=f"{job.data}")


def remove_jobs_if_exist(name: str, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """Remove jobs with given name. Returns whether job was removed."""
    current_jobs = context.job_queue.get_jobs_by_name(name)
    if not current_jobs:
        return False
    for job in current_jobs:
        job.schedule_removal()
    return True


async def schedule_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Add jobs to the queue."""
    chat_id = update.effective_message.chat_id
    try:
        word = context.args[0]  # First input parameter
        user_time = context.args[1]  # Second input parameter (HH:MM format)
        days_amount = int(context.args[2])  # Third input parameter (number of days)


        # Convert user_time to a datetime.time object
        time_parts = user_time.split(":")
        user_time_obj = time(hour=int(time_parts[0]), minute=int(time_parts[1]))

        # Get the current time and the user chat id
        now = datetime.now()
        first_execution_time = datetime.combine(now.date(), user_time_obj)
        if first_execution_time < now:
            first_execution_time += timedelta(days=1)
        delay = (first_execution_time - now).total_seconds()
        
        jobs_removed = remove_jobs_if_exist(str(chat_id), context)
        # context.job_queue.run_once(alarm, due, chat_id=chat_id, name=str(chat_id), data=due)

        for day in range(days_amount):
            job_delay = delay + day * 86400
            context.job_queue.run_once(
                schedule_callback, 
                job_delay,  # 86400 seconds in a day
                chat_id=chat_id, 
                name=str(chat_id), 
                data=word,
        )

        text = "Schedule successfully set!"
        if jobs_removed:
            text += " Old scheduled messages were removed."
        await update.effective_message.reply_text(text)

    except (IndexError, ValueError):
        await update.effective_message.reply_text("Usage: /schedule <seconds>")


async def unschedule_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Remove the jobs if the user changed their mind."""
    chat_id = update.message.chat_id
    job_removed = remove_jobs_if_exist(str(chat_id), context)
    text = "Schedule successfully cancelled!" if job_removed else "You have no active schedule."
    await update.message.reply_text(text)
