from datetime import time
from typing import List
import pickle
from dataclasses import dataclass


@dataclass
class JobData:
    book_id: str
    part: int
    chat_id: int
    time: time


DATA_FILE = "bot_jobs.pkl"


def store_jobs(jobs: List[JobData]) -> None:
    with open(DATA_FILE, "wb") as file:
        pickle.dump(jobs, file)


def retrieve_jobs() -> List[JobData]:
    with open(DATA_FILE, "rb") as file:
        return pickle.load(file)
