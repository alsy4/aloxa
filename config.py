import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "data", "aloxa.db")

# How long (seconds) before a pending reminder is marked as missed
MISSED_TIMEOUT_SECONDS = 3 * 60 * 60  # 3 hours

# How often (seconds) the scheduler checks for due reminders
SCHEDULER_POLL_INTERVAL = 30

# How long (seconds) between repeat alerts for unanswered reminders
REMINDER_REPEAT_DELAY_SECONDS = 5 * 60  # 5 minutes

# Speech recognition (Whisper)
WHISPER_MODEL = "base"
AUDIO_RATE = 16000
AUDIO_CHANNELS = 1

# Piper TTS
PIPER_MODEL_PATH = os.path.join(BASE_DIR, "models", "cori-high.onnx")
PIPER_SPEAKER_ID = None  # None = default speaker; set to int for multi-speaker models

# Ollama LLM
OLLAMA_BASE_URL = "http://localhost:11434"
OLLAMA_MODEL = "gemma3:1b"
OLLAMA_SYSTEM_PROMPT = (
    "You are Aloxa, a friendly health companion on a Raspberry Pi. "
    "You help with medication reminders, health questions, weather, time, and casual chat.\n\n"
    "RESPONSE RULES:\n"
    "- Reply in 1-2 short sentences maximum. Never use lists or bullet points.\n"
    "- Use simple, everyday words. No jargon.\n"
    "- Your responses are spoken aloud, so write exactly how you would say it.\n"
    "- Do not repeat the user's question back to them.\n"
    "- Do not fabricate medication details or dosages.\n"
    "- For health topics, add: 'Please check with your doctor.'\n"
)
