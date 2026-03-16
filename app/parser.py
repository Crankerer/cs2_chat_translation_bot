
import re

TS_CORE = r'\d{2}/\d{2}\s\d{2}:\d{2}:\d{2}'
TS = rf'{TS_CORE}\s+'
CHAT_ENTRY_RE = re.compile(
    rf'(?P<dt>{TS_CORE})\s+\[(?P<scope>ALLE|ALL|T|AT|CT)\]\s+(?P<name>[^:：]+?)\s*[:：]\s*(?P<msg>.*?)(?=(?:{TS})|\Z)',
    re.DOTALL
)

def iter_chat_entries(buffer: str):
    for m in CHAT_ENTRY_RE.finditer(buffer):
        yield (
            m.group('dt'),
            m.group('scope'),
            m.group('name').strip(),
            m.group('msg').strip(),
            m.end()
        )
