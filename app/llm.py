
import json
import requests
from .http_session import SESSION
from .util import ts

def build_system_prompt(skip_langs: list[str]) -> str:
    # primary tag normalization here keeps prompt simple
    skip_codes = sorted({(c or "").split('-')[0].strip().lower() for c in skip_langs if c})
    skip_list = ", ".join(skip_codes) if skip_codes else "(leer)"
    return (
        "Du bist ein präziser Übersetzer-Bot für CS2-Chat.\n"
        "Eingabeformat ist JSON mit den Feldern `name` und `message`.\n\n"
        "ZIEL: Antworte ausschließlich auf Deutsch – aber NUR, wenn nötig.\n\n"
        "REGELN:\n"
        f"- Bestimme die Sprache der `message` (ISO 639-1 Primärcode). SKIP_LANGS = [{skip_list}].\n"
        "- Wenn die Sprache der `message` in SKIP_LANGS ist, GIB EINE LEERE ANTWORT zurück.\n"
        "- Wenn Text nur Emotes, Satzzeichen oder Leerzeichen enthält, GIB LEER zurück.\n"
        "- Andernfalls: Übersetze ins Deutsche – ohne Einleitungen oder Erklärungen.\n"
        "- Bewahre Sinn & Ton; beleidigende Inhalte neutralisieren.\n"
        "- Gib ausschließlich den übersetzten Text zurück.\n"
    )

def call_chatgpt(api_url: str, model: str, api_key: str, temperature: float,
                 name: str, message: str, system_prompt: str, timeout_s: float = 12.0) -> str:
    if not api_key:
        print(ts(), "[LLM-Fehler] Kein API-Key (OPENAI_API_KEY oder config).")
        return ""
    payload = {
        "model": model,
        "temperature": float(temperature),
        "stream": False,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": json.dumps({"name": name, "message": message}, ensure_ascii=False)}
        ]
    }
    headers = {"Authorization": f"Bearer {api_key}"}
    try:
        res = SESSION.post(api_url, headers=headers,
                           data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
                           timeout=timeout_s)
        if res.status_code == 401:
            print(ts(), "[LLM-Fehler] 401 Unauthorized – API-Key ungültig oder fehlt.")
            return ""
        if res.status_code == 429:
            print(ts(), "[LLM-Fehler] 429 Rate limit – warte kurz.")
        res.raise_for_status()
        data = res.json()
        choice0 = (data.get("choices") or [{}])[0]
        content = ((choice0.get("message") or {}).get("content") or "").strip()
        return content
    except requests.Timeout:
        print(ts(), "[LLM-Fehler] Timeout – ggf. Timeout in config erhöhen.")
    except Exception as e:
        print(ts(), f"[LLM-Fehler] {e}")
    return ""
