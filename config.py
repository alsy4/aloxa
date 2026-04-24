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

# Intent classifier — keyword triggers that always classify as MEDICATION
MEDICATION_KEYWORDS = {
    "pill", "pills", "medicine", "medicines", "medication", "medications",
    "dose", "dosage", "took", "taken", "taking", "prescription", "prescriptions",
    "remind", "reminder", "reminders", "refill", "pharmacy",
    "tablet", "tablets", "capsule", "capsules", "drug", "drugs",
    "my meds", "my med", "did i take", "time to take", "need to take",
}

CLASSIFY_PROMPT = """\
You are a strict intent classifier. Read the user message and return exactly one label.

LABELS:
- MEDICATION — medications, reminders, dosage, pills, intake, prescriptions, drug names, "did I take", "time to take"
- HEALTH — symptoms, diseases, conditions, fitness, diet, nutrition, mental health, medical questions, side effects
- WEATHER — weather, forecast, temperature, rain, wind, humidity, sun, snow, climate, "should I bring"
- GENERAL — greetings, small talk, jokes, time, anything that does not fit the above

RULES:
1. Respond with ONLY the label — no punctuation, no explanation, no extra words.
2. If the message mentions a specific drug or pill, always use MEDICATION, even if it sounds like a health question.
3. If the message is ambiguous, pick the most specific label (MEDICATION > HEALTH > WEATHER > GENERAL).
4. Never return anything other than: MEDICATION, HEALTH, WEATHER, GENERAL.

EXAMPLES:
"What are the side effects of ibuprofen?" → MEDICATION
"What helps with a headache?" → HEALTH
"Did I take my medicine today?" → MEDICATION
"Is it going to rain tomorrow?" → WEATHER
"What's the temperature outside?" → WEATHER
"I took my paracetamol" → MEDICATION
"How are you?" → GENERAL
"Tell me a joke" → GENERAL
"Can metformin cause dizziness?" → MEDICATION
"I feel dizzy" → HEALTH
"Should I bring an umbrella?" → WEATHER
"What time is it?" → GENERAL

IMPORTANT: Your entire response must be a single word — the label only.\
"""

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
