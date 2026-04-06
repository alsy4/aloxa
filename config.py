import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "data", "aloxa.db")

# How long (seconds) before a pending reminder is marked as missed
MISSED_TIMEOUT_SECONDS = 3 * 60 * 60  # 3 hours

# How often (seconds) the scheduler checks for due reminders
SCHEDULER_POLL_INTERVAL = 30

# How long (seconds) between repeat alerts for unanswered reminders
REMINDER_REPEAT_DELAY_SECONDS = 30  # 5 minutes

# Speech recognition (Vosk)
VOSK_MODEL_PATH = os.path.join(BASE_DIR, "models", "vosk-model-small-en-us-0.15")
AUDIO_RATE = 16000
AUDIO_CHANNELS = 1

# Ollama LLM
OLLAMA_BASE_URL = "http://localhost:11434"
OLLAMA_MODEL = "qwen2.5:0.5b"
OLLAMA_SYSTEM_PROMPT = (
    "You are Aloxa, a friendly medication reminder assistant. "
    "Keep responses concise and helpful. "
    "If asked about health topics, always end with: "
    "'Note: This is not medical advice.'"
)
