
import os, time
from .util import ts

def open_follow(path: str):
    while True:
        try:
            f = open(path, "r", encoding="utf-8", errors="ignore")
            st = os.stat(path)
            f.seek(0, os.SEEK_END)
            return f, st
        except FileNotFoundError:
            print(ts(), f"[Warte] Log-Datei nicht gefunden: {path}")
            time.sleep(0.5)
