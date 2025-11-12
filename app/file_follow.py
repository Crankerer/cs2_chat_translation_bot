import os, time
from .util import ts

def open_follow(path: str, t):
    """
    Continuously attempts to open the given file until it exists.
    Once found, returns the file handle (opened for reading) and its stat info.
    Uses translated messages via t().
    """
    while True:
        try:
            f = open(path, "r", encoding="utf-8", errors="ignore")
            st = os.stat(path)
            f.seek(0, os.SEEK_END)
            return f, st
        except FileNotFoundError:
            print(ts(), t("file.wait_not_found", path=path))
            time.sleep(0.5)
