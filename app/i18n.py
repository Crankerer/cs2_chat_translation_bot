# app/i18n.py
from __future__ import annotations
import json, os
from typing import Any, Dict

_DEFAULTS: Dict[str, str] = {
    # Fallback texts (can remain empty; used as a last resort)
    "app.title": "CS2 Chat Log LLM Monitor",
    "app.header": "========================",
    "cfg.first_time": "[Info] First configuration created: {path}",
    "cfg.create_fail": "[Warning] Could not create config.json: {err}",
    "api.missing": "[Notice] No OpenAI API key found in config.json.",
    "api.saved": "[OK] OpenAI API key saved to {path}",
    "api.save_fail": "[Warning] Could not save API key: {err}",
    "api.dialog.title": "OpenAI API Key Required",
    "api.dialog.prompt": "Please enter your OpenAI API key (usually starts with 'sk-'):",
    "api.dialog.warning.empty_title": "Missing API Key",
    "api.dialog.warning.empty_msg": "No API key entered. The program will exit.",
    "api.dialog.warning.invalid_title": "Invalid Key",
    "api.dialog.warning.invalid_msg": "The key does not appear to be a valid OpenAI key.",
    "abort.no_api": "[Abort] No valid API key entered.",
    "log.hint_choose": "[Notice] log_path {hint}. Please select your Steam folder – the base before 'common' …",
    "dialog.pick_base_folder": "Select your Steam folder (base before 'common')",
    "abort.no_folder": "[Abort] No folder selected.",
    "cfg.log_saved": "[OK] log_path saved to {path}: {log}",
    "cfg.save_fail": "[Warning] Could not save config: {err}",
    "hud.title": "CS2 Chat Log LLM Monitor",
    "hud.logfile": "Log file           : {log}",
    "hud.ignore": "Ignore names       : {names}",
    "hud.gpt_api": "GPT API            : {api}",
    "hud.gpt_model": "GPT Model          : {model}",
    "hud.api_key": "API key            : {state}",
    "hud.temp": "Temperature        : {temp}",
    "hud.no_translate": "no_translate_langs : {langs}",
    "hud.poll": "Poll interval      : {ms} ms",
}

class I18N:
    def __init__(self, texts: Dict[str, str]):
        self.texts = {**_DEFAULTS, **(texts or {})}

    def t(self, key: str, **kwargs: Any) -> str:
        s = self.texts.get(key, key)  # if key is missing, display the key itself
        try:
            return s.format(**kwargs)
        except Exception:
            return s

def _load_json(path: str) -> Dict[str, str]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def load_i18n(base_dir: str, lang_code: str) -> I18N:
    # Looks for lang/lang_<code>.json with fallback to EN, then defaults
    candidates = [
        os.path.join(base_dir, "lang", f"lang_{lang_code}.json"),
        os.path.join(base_dir, "lang", "lang_en.json"),
    ]
    for p in candidates:
        if os.path.isfile(p):
            try:
                return I18N(_load_json(p))
            except Exception:
                pass
    return I18N({})
