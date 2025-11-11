
import os, json

DEFAULTS = {
    "log_path": "",
    "ignore_names": [],
    "poll_interval_ms": 100,
    "llm_api": "http://localhost:1234/v1/chat/completions",
    "llm_model": "local-model",
    "gpt_api": "https://api.openai.com/v1/chat/completions",
    "gpt_model": "gpt-4o-mini",
    "temperature": 0.2,
    "no_translate_langs": ["de"],
    "open_ai_api_key": os.environ.get("OPENAI_API_KEY", ""),
    "lang": "en"
}

def _merge_defaults(cfg: dict) -> tuple[dict, bool]:
    changed = False
    for k, v in DEFAULTS.items():
        if k not in cfg:
            cfg[k] = v
            changed = True
    return cfg, changed

def load_config(path: str) -> dict:
    # 1) Datei lesen (resilient)
    try:
        with open(path, "r", encoding="utf-8") as f:
            cfg = json.load(f)
            if not isinstance(cfg, dict):
                cfg = {}
    except FileNotFoundError:
        cfg = {}
    except Exception:
        cfg = {}

    # 2) Defaults einmischen (Migration alter Dateien)
    cfg, changed = _merge_defaults(cfg)

    # 3) API-Key ggf. aus Datei laden
    key_file = (cfg.get("open_ai_api_key_file") or "").strip()
    if not (cfg.get("open_ai_api_key") or "").strip() and key_file:
        try:
            with open(key_file, "r", encoding="utf-8") as fh:
                cfg["open_ai_api_key"] = fh.read().strip()
                changed = True
        except Exception:
            pass

    # 4) log_path normalisieren (vermindert gemischte Slashes)
    lp = cfg.get("log_path", "")
    if isinstance(lp, str) and lp:
        norm_lp = os.path.normpath(lp)
        if norm_lp != lp:
            cfg["log_path"] = norm_lp
            changed = True

    # 5) Migration zurückschreiben, wenn sich was geändert hat
    if changed:
        try:
            save_config(path, cfg)
        except Exception:
            pass

    return cfg

def save_config(path: str, cfg: dict) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=2, ensure_ascii=False)