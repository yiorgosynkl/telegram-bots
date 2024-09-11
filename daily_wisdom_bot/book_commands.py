#!/usr/bin/env python

import logging
from typing import List
from datetime import datetime, time, timedelta
from telegram import Update
from telegram.ext import ContextTypes

from utils import (
    get_books,
    get_book,
    get_part,
    BookData,
    InvalidBookError,
    InvalidPartError,
)
from job_utils import JobData, store_jobs, retrieve_jobs


async def start_up_callback(context: ContextTypes.DEFAULT_TYPE):
    job_datas = retrieve_jobs()
    for job_data in job_datas:
        if job_data:
            add_job(context=context, job_data=job_data)


async def periodic_save_callback(context):
    job_datas = [job.data for job in context.job_queue.jobs()]
    store_jobs(job_datas)
    # logging.info(f"Completed periodic save of jobs. {job_datas=}")


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


def get_jobs(
    context: ContextTypes.DEFAULT_TYPE, chat_id: int, book_id: str = None
) -> List[JobData]:
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


# telegram limit is 4096 characters
# further more, I shouldn't send more than 30 messages, othwerwise it leads to timeout
def split_in_texts(msg: str, max_length: int = 4000):  # 4096 the limit in telegram
    def split_with_limit(text: str, max_length: int) -> List[str]:
        if len(text) < max_length:
            return [text]
        chunks = []
        current_chunk = ""
        for word in text.split(" "):
            if word == "":
                continue
            if len(current_chunk) + len(word) + 1 > max_length:
                chunks.append(current_chunk.strip())
                current_chunk = ""
            current_chunk += word + " "
        if current_chunk:
            chunks.append(current_chunk.strip())
        return chunks

    # replace \n\n with \n and \n with spaces
    new_msg = "\n".join([l.replace("\n", " ") for l in msg.split("\n\n") if l != ""])
    return split_with_limit(new_msg, max_length)


async def job_callback(context: ContextTypes.DEFAULT_TYPE) -> None:
    job = context.job
    job_data = job.data
    book_data = get_book(job_data.book_id)
    full_text = get_part(book_id=job_data.book_id, part=job_data.part)
    texts = split_in_texts(full_text)
    for text in texts:
        await context.bot.send_message(job_data.chat_id, text=text)
    if 1 <= job_data.part + 1 <= book_data.max_part:
        job_data.part += 1
        add_job(context, job_data)
    else:
        await context.bot.send_message(
            job.chat_id,
            text="Congrats, this was the last part of the series, you just completed this series :)",
        )


def get_delay(time):
    now = datetime.now()
    first_execution_time = datetime.combine(now.date(), time)
    if first_execution_time < now:
        first_execution_time += timedelta(days=1)
    delay = (first_execution_time - now).total_seconds()
    return delay


def parse_book(tag: str) -> BookData:
    book_tags = {b.tag: b for b in get_books()}  # tag to book id
    if tag not in book_tags:
        raise InvalidBookError
    return book_tags[tag]


def parse_time(s):
    time_parts = s.split(":")
    return time(hour=int(time_parts[0]), minute=int(time_parts[1]))


def parse_part(part: int, book_data: BookData) -> int:
    if 1 <= part <= book_data.max_part:
        return part
    raise InvalidPartError


async def begin_series_command(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    try:
        chat_id = update.effective_message.chat_id
        book_data = parse_book(
            context.args[0]
        )  # First input parameter (book_id), TODO: mapping arg to ids
        user_time = parse_time(context.args[1])  # Second input parameter (HH:MM format)
        book_part = parse_part(
            int(context.args[2]) if len(context.args) >= 3 else 1, book_data
        )  # Optional third input parameter (starting part)

        job_data = JobData(
            chat_id=chat_id, book_id=book_data.id, time=user_time, part=book_part
        )

        did_remove_old_jobs = add_job(context, job_data)

        text = f"You succussfully set a daily schedule to read {book_data.name} by {book_data.author}."
        text += f"\nNext message will be at {user_time.hour:02d}:{user_time.minute:02d}"
        if did_remove_old_jobs:
            text += " (Old schedule was removed)."
        await update.effective_message.reply_text(text)

    except InvalidBookError:
        await update.effective_message.reply_text(
            "This series doesn't exist. Check the available series with /view_series."
        )
    except InvalidPartError:
        await update.effective_message.reply_text(
            "This part number doesn't exist for this series."
        )
    except (IndexError, ValueError):
        await update.effective_message.reply_text(
            "Usage: /begin <book> <HH:MM> <?part>"
        )


async def upcoming_series_command(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    try:
        chat_id = update.effective_message.chat_id
        book_id = (
            context.args[0] if len(context.args) >= 1 else None
        )  # Optional irst input parameter (book_id)
        jobs = get_jobs(context, chat_id=chat_id, book_id=book_id)
        if len(jobs) == 0:
            await update.effective_message.reply_text("No messages scheduled")
            return

        def repr_job(job):
            book_data = get_book(book_id=job.data.book_id)
            return f"Part {job.data.part} of {book_data.name} by {book_data.author} will be delivered at {job.data.time.hour:02d}:{job.data.time.minute:02d}"

        text = "Upcoming messages: "
        text += "\n* " + "\n* ".join([repr_job(job) for job in jobs])
        await update.effective_message.reply_text(
            text if text else "No messages scheduled"
        )
    except (IndexError, ValueError):
        await update.effective_message.reply_text("Usage: /check_series <?book>")


async def end_series_command(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    try:
        chat_id = update.effective_message.chat_id
        book_id = (
            context.args[0] if len(context.args) >= 1 else None
        )  # Optional first input parameter (book_id)
        did_remove_jobs = remove_jobs(context, chat_id=chat_id, book_id=book_id)
        await update.effective_message.reply_text(
            f"Successfully removed scheduled messages for {book_id if book_id else 'all book'} series"
            if did_remove_jobs
            else "No relevant scheduled messages found"
        )
    except (IndexError, ValueError):
        await update.effective_message.reply_text("Usage: /end <?book>")


async def view_series_command(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    try:
        books = get_books()
        text = "The following books exists in the library:"
        text += "\n* " + "\n* ".join(
            [f"{b.tag} : {b.name} by {b.author} ({b.max_part} parts)" for b in books]
        )
        text += "\nUse these names to select the series of your choice."
        text += "\nType something like `/begin zrb 08:00`. Happy reading :)"
        await update.effective_message.reply_text(text)
    except (IndexError, ValueError):
        await update.effective_message.reply_text("Usage: /view")
