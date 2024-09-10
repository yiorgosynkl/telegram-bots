from os import environ
from pathlib import Path
from dataclasses import dataclass
from typing import List
import re

FILE_STEM_LG = 3
FILE_REGEX_PATTERN = r"\d{3}.txt"


@dataclass
class BookData:
    id: str
    name: str
    author: str
    tag: str
    dir_name: str
    max_part: int


def get_books() -> List[BookData]:
    def parse_title(dir_name):
        book_id, name, author, tag = dir_name.split("-")
        pth = Path(environ["BOOK_COLLECTION_PATH"]) / dir_name
        max_part = int(
            max(
                f.stem
                for f in pth.iterdir()
                if f.is_file() and bool(re.match(FILE_REGEX_PATTERN, f.name))
            )
        )
        return BookData(
            id=book_id,
            name=name,
            author=author,
            tag=tag,
            dir_name=dir_name,
            max_part=max_part,
        )

    pth = Path(environ["BOOK_COLLECTION_PATH"])
    books = [
        parse_title(entry.name)
        for entry in pth.iterdir()
        if entry.is_dir() and len(entry.name.split("-")) == 4
    ]
    return books


def get_book(book_id: str) -> BookData:
    book_dir = {b.id: b for b in get_books()}
    if book_id not in book_dir.keys():
        raise InvalidBookError
    return book_dir[book_id]


def get_parts_stems(book_id: str):
    pth = Path(environ["BOOK_COLLECTION_PATH"]) / get_book(book_id).dir_name
    files = [f.stem for f in pth.iterdir() if f.is_file()]
    return files


def get_part(book_id: str, part: int):
    book_data = get_book(book_id=book_id)
    if part < book_data.max_part:
        raise InvalidPartError
    filestem = str(part).zfill(FILE_STEM_LG)
    pth = (
        Path(environ["BOOK_COLLECTION_PATH"])
        / get_book(book_id).dir_name
        / f"{filestem}.txt"
    )
    with open(pth) as f:
        return f.read()


class InvalidBookError(Exception):
    pass


class InvalidPartError(Exception):
    pass
