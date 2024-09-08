#!/usr/bin/env python

from datetime import datetime, time, timedelta
from telegram import Update
from telegram.ext import ContextTypes

from dataclasses import dataclass


@dataclass
class JobData:
    book_id: str
    part: int
    chat_id: int
    time: time


# job_id: <chat_id> <book>
def get_jobs(
    context: ContextTypes.DEFAULT_TYPE, chat_id: int, book_id: str = None
):  # -> List[Jobs]
    current_jobs = context.job_queue.get_jobs_by_name(str(chat_id))
    if book_id == None:
        return current_jobs
    return tuple(job for job in current_jobs if job.data.book_id == book_id)


def remove_jobs(
    context: ContextTypes.DEFAULT_TYPE, chat_id: int, book_id: str = None
) -> bool:
    current_jobs = get_jobs(context, chat_id, book_id)
    if len(current_jobs) == 0:
        return False
    for job in current_jobs:
        job.schedule_removal()
    return True


async def job_callback(context: ContextTypes.DEFAULT_TYPE) -> None:
    job = context.job
    job_data = job.data
    # TODO: search actual libary
    await context.bot.send_message(job.chat_id, text=f"Get message for {job_data}")
    # update for next job, if part exists
    job_data.part += 1
    add_job(context, job_data)


def get_delay(time):
    now = datetime.now()
    first_execution_time = datetime.combine(now.date(), time)
    if first_execution_time < now:
        first_execution_time += timedelta(days=1)
    delay = (first_execution_time - now).total_seconds()
    return delay


# only one job per <chat_id>+<book> is allowed in the queue
def add_job(context: ContextTypes.DEFAULT_TYPE, job_data: JobData):
    did_remove_jobs = remove_jobs(
        context, chat_id=job_data.chat_id, book_id=job_data.book_id
    )
    job_delay = get_delay(job_data.time)
    context.job_queue.run_once(
        job_callback,
        job_delay,
        chat_id=job_data.chat_id,
        name=str(job_data.chat_id),
        data=job_data,
    )
    return did_remove_jobs


def parse_time(s):
    time_parts = s.split(":")
    return time(hour=int(time_parts[0]), minute=int(time_parts[1]))


async def start_series_command(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    try:
        chat_id = update.effective_message.chat_id
        book_id = context.args[
            0
        ]  # First input parameter (book_id), TODO: mapping arg to ids
        user_time = parse_time(context.args[1])  # Second input parameter (HH:MM format)
        book_part = (
            int(context.args[2]) if len(context.args) >= 3 else 0
        )  # Optional third input parameter (starting part)

        job_data = JobData(
            chat_id=chat_id, book_id=book_id, time=user_time, part=book_part
        )

        did_remove_old_jobs = add_job(context, job_data)

        text = f"You succussfully set a daily schedule to read {book_id}, next message will be at {user_time}"
        if did_remove_old_jobs:
            text += " (Old schedule was removed)."
        await update.effective_message.reply_text(text)

    except (IndexError, ValueError):
        await update.effective_message.reply_text(
            "Usage: /start_series <book> <HH:MM> <?part>"
        )


async def check_series_command(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    try:
        chat_id = update.effective_message.chat_id
        book_id = (
            context.args[0] if len(context.args) >= 1 else None
        )  # Optional irst input parameter (book_id)
        jobs = get_jobs(context, chat_id=chat_id, book_id=book_id)
        text = " & ".join([str(job.data) for job in jobs])
        await update.effective_message.reply_text(
            text if text else "No messages scheduled"
        )
    except (IndexError, ValueError):
        await update.effective_message.reply_text("Usage: /check_series <?book>")


async def stop_series_command(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    try:
        chat_id = update.effective_message.chat_id
        book_id = (
            context.args[0] if len(context.args) >= 0 else None
        )  # Optional irst input parameter (book_id)
        did_remove_jobs = remove_jobs(context, chat_id=chat_id, book_id=book_id)
        await update.effective_message.reply_text(
            f"Successfully removed scheduled messages for {book_id if book_id else 'all book'} series"
            if did_remove_jobs
            else "No relevant scheduled messages found"
        )
    except (IndexError, ValueError):
        await update.effective_message.reply_text("Usage: /stop_series <?book>")
