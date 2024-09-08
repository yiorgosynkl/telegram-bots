from os import environ
from pathlib import Path

FILE_STEM_LG = 3


def get_books():
    pth = Path(environ["BOOK_COLLECTION_PATH"])
    dirs = [entry.name for entry in pth.iterdir() if entry.is_dir()]
    return dirs


def get_parts_stems(book: str):
    pth = Path(environ["BOOK_COLLECTION_PATH"]) / book
    files = [f.stem for f in pth.iterdir() if f.is_file()]
    return files


def is_part_valid(book: str, part: int):
    files = get_parts_stems(book)
    mn_file, mx_file = min(files), max(files)
    return int(mn_file) <= part <= int(mx_file)


def get_part(book: str, part: int):
    filestem = str(part).zfill(FILE_STEM_LG)
    if filestem not in get_parts_stems(book):
        raise InvalidPartError
    pth = Path(environ["BOOK_COLLECTION_PATH"]) / book / f"{filestem}.txt"
    with open(pth) as f:
        return f.read()


class InvalidBookError(Exception):
    pass


class InvalidPartError(Exception):
    pass
