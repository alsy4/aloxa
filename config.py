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
    "The user will ask health-related questions. You may also receive their current medication list for context, "
    "and trusted NHS reference passages retrieved for their question.\n\n"
    "RESPONSE RULES:\n"
    "- Reply in 1-3 short sentences maximum. No lists or bullet points.\n"
    "- Use simple, everyday words. No jargon.\n"
    "- Your responses are spoken aloud, so write exactly how you would say it.\n"
    "- Do not fabricate medication details or dosages.\n"
    "- If REFERENCE INFORMATION is provided, base your answer strictly on it. "
    "If the reference does not cover the question, say you're not sure and suggest they check with their doctor.\n"
    "- If no REFERENCE INFORMATION is provided, give a brief general answer and still remind them to check with their doctor.\n"
    "- Always end with: 'Please check with your doctor.'\n"
    "- DO NOT USE EMOJIS \n"
)

# Ollama LLM
OLLAMA_BASE_URL = "http://localhost:11434"
OLLAMA_MODEL = "qwen2.5:0.5b"

# Intent classifier — unambiguous CRUD / intake-logging phrases that
# short-circuit to MEDICATION without hitting the LLM. Knowledge-style
# drug terms ("dose", "pill", "medicine", "prescription", etc.) are
# intentionally excluded so they flow to the LLM and get routed to HEALTH.
MEDICATION_KEYWORDS = {
    "took", "taken", "taking",
    "my meds", "my med",
    "did i take", "time to take", "need to take",
    "remind", "reminder", "reminders",
}

CLASSIFY_PROMPT = """\
You are a strict intent classifier. Read the user message and return exactly one label.

LABELS:
- MEDICATION — ONLY for managing the user's own medication records (CRUD) and intake logging.
    Examples of MEDICATION intent:
      * adding, removing, updating, or listing their scheduled medications
      * asking what medications they take or when they're due
      * logging that they took a dose, or asking whether they took one
- HEALTH — all medical knowledge questions, including: side effects, drug information, how/when
  a medication or vitamin should be taken, what a medication is for, drug interactions,
  vitamin and mineral information, symptoms, diseases, conditions, fitness, diet, nutrition,
  mental health. Drug names in a knowledge question belong here, NOT in MEDICATION.
- WEATHER — weather, forecast, temperature, rain, wind, humidity, sun, snow, climate, "should I bring"
- GENERAL — greetings, small talk, jokes, time, anything that does not fit the above

RULES:
1. Respond with ONLY the label — no punctuation, no explanation, no extra words.
2. MEDICATION is strictly for CRUD and intake-log actions on the user's own medication records.
   Any question about what a drug does, how it works, its side effects, how/when to take it,
   interactions, or vitamin/mineral guidance is HEALTH — even if the user names a specific drug.
3. If the user is logging or asking about their own intake ("I took X", "did I take X today",
   "time to take X", "remind me to take X"), classify as MEDICATION.
4. If ambiguous, prefer HEALTH over MEDICATION for any knowledge-seeking question.
5. Never return anything other than: MEDICATION, HEALTH, WEATHER, GENERAL.

EXAMPLES:
"What are the side effects of ibuprofen?" → HEALTH
"Can metformin cause dizziness?" → HEALTH
"How should I take my ramipril?" → HEALTH
"When is the best time to take vitamin D?" → HEALTH
"What foods contain iron?" → HEALTH
"What is paracetamol used for?" → HEALTH
"What helps with a headache?" → HEALTH
"I feel dizzy" → HEALTH
"Add paracetamol 500mg at 8am and 8pm" → MEDICATION
"List my medications" → MEDICATION
"What medications am I on?" → MEDICATION
"Remove ibuprofen from my list" → MEDICATION
"Did I take my medicine today?" → MEDICATION
"I took my paracetamol" → MEDICATION
"Time to take my metformin?" → MEDICATION
"Is it going to rain tomorrow?" → WEATHER
"Should I bring an umbrella?" → WEATHER
"What's the temperature outside?" → WEATHER
"How are you?" → GENERAL
"Tell me a joke" → GENERAL
"What time is it?" → GENERAL

IMPORTANT: Your entire response must be a single word — the label only.\
"""

# Health RAG
HEALTH_CORPUS_DIR = os.path.join(BASE_DIR, "data", "health_corpus")
HEALTH_INDEX_PATH = os.path.join(BASE_DIR, "data", "health_index.db")
HEALTH_EMBED_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
HEALTH_EMBED_DIM = 384
HEALTH_CHUNK_MAX_CHARS = 800
HEALTH_RETRIEVAL_K = 3
HEALTH_RETRIEVAL_MIN_SCORE = 0.35

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
