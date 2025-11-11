
from datetime import datetime

ZERO_WIDTH_TABLE = dict.fromkeys(map(ord, [
    '\u200b','\u200c','\u200d','\u2060','\ufeff',
    '\u200e','\u200f','\u202a','\u202b','\u202c','\u202d','\u202e'
]), None)

def ts() -> str:
    return datetime.now().strftime("[%H:%M:%S]")

def primary_lang_tag(code: str) -> str:
    return (code or "").split('-')[0].strip().lower()

def normalize(s: str) -> str:
    return s.translate(ZERO_WIDTH_TABLE) if s else s
