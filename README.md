An Overview File for Aloxa

## Voice Conversation Flow

Below is the full flow when a user speaks to Aloxa (option 9 in the menu):

```
User speaks into microphone
│
├─ main.py:36 — User selects option 9
│   └─ calls start_voice_conversation(manager)
│
└─ voice/conversation.py:105 — start_voice_conversation()
    │
    ├─ :113 — manager.get_all_medications()
    │   └─ medication/manager.py:31 — queries DB for all medication names
    │
    ├─ :114 — SpeechListener(medication_names=["Paracetamol", ...])
    │   └─ voice/listener.py:24 — __init__()
    │       ├─ :26 — WhisperModel("base", device="cpu", compute_type="int8")
    │       └─ :28 — set_medication_names() → builds initial_prompt string
    │
    ├─ :115 — OllamaClient()
    │   └─ llm/ollama_client.py:9 — __init__() with model + system prompt from config.py
    │
    └─ LOOP (:120)
        │
        ├─ :121 — listener.listen()
        │   └─ voice/listener.py:35 — listen()
        │       ├─ :41 — Opens PyAudio stream (16kHz, mono)
        │       ├─ :55 — Records audio frames until silence detected
        │       │         (RMS > 500 = speech, 30 silent chunks = stop)
        │       ├─ :80 — Writes frames to temp .wav file
        │       ├─ :87 — model.transcribe(wav, language="en", initial_prompt="Paracetamol, ...")
        │       │         └─ faster-whisper returns segments
        │       ├─ :90 — Joins segments into text string
        │       └─ :91 — _fix_medication_names(text)
        │           └─ :93 — Fuzzy-matches words against known medication names
        │                    using difflib.get_close_matches (cutoff=0.6)
        │
        ├─ :125 — Prints "You: {text}"
        │
        ├─ :127 — Exit check ("stop", "exit", "quit", "bye", "goodbye")
        │
        ├─ :131 — classify_intent(text)
        │   └─ llm/intent_classifier.py:38 — classify_intent()
        │       ├─ Sends text to Ollama with CLASSIFY_PROMPT
        │       │   └─ POST http://localhost:11434/api/chat
        │       └─ Returns one of: MEDICATION, HEALTH, WEATHER, GENERAL
        │
        └─ ROUTING (:134)
            │
            ├─ HEALTH → :136 — "Routing to Watson API..." (stub)
            │
            ├─ WEATHER → :139 — "Routing to Weather API..." (stub)
            │
            ├─ MEDICATION → :141
            │   ├─ _build_medication_context(manager)
            │   │   └─ voice/conversation.py:30
            │   │       ├─ manager.get_all_medications()  → medication/manager.py:31
            │   │       ├─ manager.get_all_intake_history() → medication/manager.py:203
            │   │       └─ manager.get_pending_reminders() → medication/manager.py:214
            │   │       Returns formatted context string with meds, logs, pending
            │   │
            │   ├─ client.chat(text, extra_context=context)
            │   │   └─ llm/ollama_client.py:14 — chat()
            │   │       ├─ Appends to conversation history
            │   │       ├─ POST http://localhost:11434/api/chat
            │   │       │   (system prompt + medication context + history)
            │   │       └─ Returns LLM reply
            │   │
            │   └─ _process_taken_tags(reply, manager)
            │       └─ voice/conversation.py:79
            │           ├─ Finds [TAKEN: medication_name] tags in reply
            │           ├─ manager.get_pending_reminders() → medication/manager.py:214
            │           ├─ manager.mark_taken(log_id) → medication/manager.py:143
            │           └─ Strips tags, returns clean reply
            │
            └─ GENERAL → :147
                └─ client.chat(text)  — no medication context injected
                    └─ llm/ollama_client.py:14

        └─ :149 — Prints "Aloxa: {reply}"
            └─ Back to top of LOOP
```

### Summary

There are two Ollama calls per turn:

1. **Intent classification** (`llm/intent_classifier.py`) — lightweight, no history, just returns a label
2. **Response generation** (`llm/ollama_client.py`) — stateful with conversation history, only for MEDICATION and GENERAL intents
