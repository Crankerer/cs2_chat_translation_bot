
import os, time, collections, threading
from concurrent.futures import ThreadPoolExecutor
from .util import ts, normalize
from .parser import iter_chat_entries
from .file_follow import open_follow
from .llm import build_system_prompt, call_chatgpt

def should_ignore(name: str, ignore_names: list[str]) -> bool:
    n = normalize(name).casefold()
    return any(n == normalize(x).casefold() for x in ignore_names)

def start_tail_thread(log_path: str, ignore_names: list[str], poll_ms: int, cfg: dict,
                      emit_structured, pool: ThreadPoolExecutor) -> threading.Thread:
    def _worker():
        f, st_prev = open_follow(log_path)
        last_inode = getattr(st_prev, "st_ino", None)
        buffer = ""
        system_prompt = build_system_prompt(cfg.get("no_translate_langs", []))
        last_calls = collections.deque(maxlen=10)

        print(ts(), "Überwachung gestartet — Übersetze nur bei Bedarf.\n")

        while True:
            try:
                chunk = f.read()
                if chunk:
                    buffer += chunk
                    last_end = 0
                    for dt, scope, name, msg, endpos in iter_chat_entries(buffer):
                        if should_ignore(name, ignore_names):
                            last_end = endpos; continue

                        # sanftes Rate-Limiting
                        now = time.time()
                        if len(last_calls) == last_calls.maxlen and now - last_calls[0] < 1.0:
                            time.sleep(0.1)
                        last_calls.append(now)

                        fut = pool.submit(
                            call_chatgpt,
                            cfg["gpt_api"], cfg["gpt_model"],
                            cfg.get("open_ai_api_key", ""),
                            float(cfg.get("temperature", 0.2)),
                            name, msg, system_prompt
                        )

                        def deliver(fut, dt=dt, scope=scope, name=name):
                            translated = fut.result() or ""
                            if translated:
                                try:
                                    emit_structured(dt, scope, name, translated)
                                except Exception:
                                    pass
                        fut.add_done_callback(deliver)
                        last_end = endpos

                    if last_end:
                        buffer = buffer[last_end:]
                    if len(buffer) > 2_000_000:
                        buffer = buffer[-1_000_000:]

                else:
                    try:
                        st_now = os.stat(log_path)
                    except FileNotFoundError:
                        try: f.close()
                        except Exception: pass
                        print(ts(), "[Info] Log-Datei nicht verfügbar. Warte…")
                        f, st_prev = open_follow(log_path)
                        last_inode = getattr(st_prev, "st_ino", None)
                        buffer = ""
                        time.sleep(poll_ms / 1000)
                        continue

                    current_inode = getattr(st_now, "st_ino", None)
                    current_size = st_now.st_size
                    pos = f.tell()
                    rotated = (current_inode and last_inode and current_inode != last_inode)
                    truncated = current_size < pos

                    if rotated or truncated:
                        try: f.close()
                        except Exception: pass
                        print(ts(), f"[Info] Log-{'Rotation' if rotated else 'Truncation'} erkannt – öffne neu.")
                        f, st_prev = open_follow(log_path)
                        last_inode = getattr(st_prev, "st_ino", None)
                        buffer = ""
                    else:
                        time.sleep(poll_ms / 1000)

            except KeyboardInterrupt:
                print("\n", ts(), "Beendet durch Benutzer (Strg+C).")
                try: f.close()
                except Exception: pass
                break
            except Exception as e:
                print(ts(), f"[Fehler] {e!r}")
                time.sleep(poll_ms / 1000)

    t = threading.Thread(target=_worker, daemon=True)
    t.start()
    return t
