
# CS2 Chat HUD Übersetzer (modular)

Diese Version teilt den Code in mehrere, klar abgegrenzte Module auf:

```
cs2_chat_hud/
├─ app/
│  ├─ __init__.py
│  ├─ config.py           # Laden/Validieren der Konfiguration
│  ├─ util.py             # Hilfsfunktionen (Timestamp, Normalisierung, etc.)
│  ├─ http_session.py     # Requests-Session mit Retry/Backoff
│  ├─ llm.py              # OpenAI-kompatibler Chat-Call
│  ├─ parser.py           # Regex/Parsing für Chatzeilen
│  ├─ file_follow.py      # Robustes Tail der Log-Datei (Rotation/Truncation)
│  ├─ hud.py              # Tkinter HUD (inkl. Close-Button ✕)
│  ├─ tailer.py           # Tailing + LLM-Worker + Emission in HUD
│  └─ main.py             # Einstiegspunkt
├─ requirements.txt
└─ config.sample.json
```

## Start

1. Erstelle deine `config.json` basierend auf `config.sample.json`.
2. Installiere Abhängigkeiten:
   ```bash
   pip install -r requirements.txt
   ```
3. Starten:
   ```bash
   python -m app.main  # oder: python app/main.py
   ```
