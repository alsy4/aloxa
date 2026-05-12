# Aloxa

Aloxa is a Raspberry Pi 5 medication-reminder companion. It tracks your medications, reminds you when to take them, logs whether each dose was taken or missed, and answers health, weather, and general questions through a voice or text conversation powered by a local LLM, cloud LLM, and a local health-knowledge RAG index.

## What It Does

- Stores medications (name, dosage, information) and their scheduled times (HH:MM).
- Generates a reminder event for every scheduled dose and tracks it through `pending → taken | missed` (auto-expires to `missed` after 3 hours).
- Listens to the user through a USB microphone, transcribes speech with Whisper, classifies the intent, routes the request to the right backend (medication DB, health RAG + WatsonX, weather API, or local Ollama small-talk), and speaks the reply back through Piper TTS.
- Drives per-compartment servos and LEDs so the correct medication compartment opens and lights up at reminder time.

## Features

- **Medication CRUD + intake logging** — add, update, delete medications and scheduled times; every reminder is logged.
- **Reminder scheduler** (`medication/scheduler.py`) — polls every 30s, repeats unanswered alerts every 5min, expires pending events after 3h.
- **Voice conversation** (menu option 9) — STT → intent classifier → routed reply → TTS.
- **Text conversation** (menu option 10) — same routing pipeline without audio.
- **Intent routing** — `MEDICATION`, `HEALTH`, `WEATHER`, `GENERAL`, with a keyword short-circuit list for medication queries.
- **Health RAG** — local SQLite vector index over an NHS corpus, MiniLM embeddings, top-k=3, min score 0.35, fed into the WatsonX prompt.
- **`[TAKEN: <med>]` tag parsing** — the LLM can mark a dose as taken inside its reply; the tag is stripped and `mark_taken` is called.
- **Hardware control** — servo per compartment (`compartment_servos.py`) and LED per compartment (`compartment_leds.py`).
- **Front-ends** — CLI menu (`main.py`) and TUI (`tui.py`).

## Technologies

- **Language / runtime:** Python 3 on Raspberry Pi 5 (Linux).
- **Storage:** SQLite — `data/aloxa.db` (app data) and `data/health_index.db` (RAG vector index).
- **STT:** `faster-whisper` (configurable model) at 16kHz mono via PyAudio. Vosk is also bundled as a legacy alternative.
- **TTS:** `piper-tts` with `en_GB-northern_english_male-medium.onnx` and a custom `cori-med.onnx` voice.
- **Local LLM:** Ollama at `http://localhost:11434` running `qwen2.5:0.5b` (intent classification and `GENERAL` / `MEDICATION` replies).
- **Cloud LLM:** IBM WatsonX (`mistralai/mistral-small-3-1-24b-instruct-2503`, EU-GB region) for `HEALTH` replies.
- **Embeddings:** `sentence-transformers/all-MiniLM-L6-v2` (384-dim).
- **Weather:** weatherapi.com, default location Sheffield.
- **Audio I/O:** PyAudio.
- **Secrets:** `.env` — `WATSONX_API_KEY`, `WATSONX_PROJECT_ID`, `WEATHER_API_KEY`.

## Hardware

- MINI USB Microphone.
- One servo per medication compartment.
- One LED per medication compartment.

## Project Layout

- `config.py` — central constants (DB paths, timeouts, model names, prompts, API URLs).
- `database/` — SQLite connection and `schema.sql`. Tables: `medications`, `medication_times`, `intake_log`.
- `medication/` — data model, CRUD + intake logging, reminder scheduler, CLI helpers, intake parser.
- `voice/` — Whisper listener with medication-name fuzzy fix, Piper TTS, voice/text conversation loop.
- `llm/` — Ollama chat client, intent classifier, WatsonX client, health retriever (RAG).
- `weather/` — weatherapi.com client.
- `scripts/` — offline builders for the NHS health corpus and the RAG index.
- `models/` — Piper voice ONNX files.
- `tests/` — CRUD/unit tests with `conftest.py` fixtures.
- `diagram/` — drawio files (system flow, class architecture, ERD, RAG, STT/TTS, intent classifier, use cases, Pi connections, power-interest grid).
- `main.py` — entry point and CLI menu.

## Running

```bash
python3 main.py
```

## Testing

```bash
pytest
```

The CRUD/unit test suite covers 20+ tests and uses isolated temporary databases via `tests/conftest.py`.

### Summary

There are two Ollama calls per turn:

1. **Intent classification** (`llm/intent_classifier.py`) — lightweight, no history, just returns a label.
2. **Response generation** (`llm/ollama_client.py`) — stateful with conversation history, only for `MEDICATION` and `GENERAL` intents.
