import os

from dotenv import load_dotenv

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(BASE_DIR, ".env"))
DB_PATH = os.path.join(BASE_DIR, "data", "aloxa.db")

# How long (seconds) before a pending reminder is marked as missed
MISSED_TIMEOUT_SECONDS = 3 * 60 * 60  # 3 hours

# How often (seconds) the scheduler checks for due reminders
SCHEDULER_POLL_INTERVAL = 30

# How long (seconds) between repeat alerts for unanswered reminders
REMINDER_REPEAT_DELAY_SECONDS = 5 * 60  # 5 minutes

# Speech recognition (Whisper)
WHISPER_MODEL = "tiny"
AUDIO_RATE = 16000
AUDIO_CHANNELS = 1

# Piper TTS
PIPER_MODEL_PATH = os.path.join(BASE_DIR, "models", "cori-med.onnx")
PIPER_SPEAKER_ID = None  # None = default speaker; set to int for multi-speaker models

# Weather API (weatherapi.com)
WEATHER_API_KEY = os.getenv("WEATHER_API_KEY", "")
WEATHER_API_URL = "http://api.weatherapi.com/v1"
WEATHER_DEFAULT_LOCATION = os.getenv("WEATHER_DEFAULT_LOCATION", "Sheffield")

# WatsonX API (health queries)
WATSONX_API_KEY = os.getenv("WATSONX_API_KEY", "")
WATSONX_PROJECT_ID = os.getenv("WATSONX_PROJECT_ID", "")
WATSONX_URL = "https://eu-gb.ml.cloud.ibm.com"
WATSONX_MODEL = "mistralai/mistral-small-3-1-24b-instruct-2503"
WATSONX_HEALTH_SYSTEM_PROMPT = (
    "You are Aloxa, a friendly health companion on a Raspberry Pi. "
    "The user will ask health-related questions. You may also receive their current medication list for context.\n\n"
    "RESPONSE RULES:\n"
    "- Reply in 1-3 short sentences maximum. No lists or bullet points.\n"
    "- Use simple, everyday words. No jargon.\n"
    "- Your responses are spoken aloud, so write exactly how you would say it.\n"
    "- Do not fabricate medication details or dosages.\n"
    "- Always end with: 'Please check with your doctor.'\n"
    "- DO NOT USE EMOJIS \n"
)

# Ollama LLM
OLLAMA_BASE_URL = "http://localhost:11434"
OLLAMA_MODEL = "qwen2.5:0.5b"
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
