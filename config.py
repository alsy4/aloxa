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
PIPER_MODEL_PATH = os.path.join(BASE_DIR, "models", "en_GB-northern_english_male-medium.onnx")
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
You are an intent classification engine.

Classify the user's message into EXACTLY ONE label:

- MEDICATION
- HEALTH
- WEATHER
- GENERAL

DEFINITIONS

MEDICATION
Only for actions involving the user's OWN medication records or medication intake tracking.

Includes:
- adding medications
- removing medications
- updating medication schedules
- listing medications
- asking what medications they take
- asking when medications are due
- logging medication intake
- asking whether they already took a medication
- reminders related to taking medications

Examples:
- "Add paracetamol at 8am"
- "Remove ibuprofen"
- "What meds am I taking?"
- "Did I take my metformin today?"
- "Log that I took aspirin"
- "When is my next dose?"

HEALTH
All medical, wellness, fitness, nutrition, symptom, disease, or drug-information questions.

Includes:
- medication side effects
- drug usage guidance
- drug purpose
- drug interactions
- vitamins and supplements
- symptoms
- conditions and diseases
- exercise and fitness
- diet and nutrition
- mental health
- general medical advice

IMPORTANT:
If the user is SEEKING INFORMATION about a medication, classify as HEALTH — NOT MEDICATION.

Examples:
- "What is ibuprofen used for?"
- "Can metformin cause nausea?"
- "How should I take vitamin D?"
- "What are symptoms of flu?"
- "I feel dizzy"
- "Does magnesium help sleep?"

WEATHER
Anything related to:
- forecasts
- rain
- temperature
- snow
- wind
- humidity
- climate
- clothing decisions based on weather

Examples:
- "Will it rain tomorrow?"
- "Should I bring an umbrella?"
- "What's the weather outside?"

GENERAL
Anything that does not fit the categories above.

Examples:
- greetings
- jokes
- casual conversation
- time/date questions
- non-health knowledge questions

Examples:
- "Hello"
- "Tell me a joke"
- "What time is it?"

DECISION RULES

1. Return EXACTLY ONE label.
2. Output ONLY the label.
3. No punctuation.
4. No explanation.
5. If the message is about medication INFORMATION or ADVICE → HEALTH.
6. If the message is about medication TRACKING or RECORD MANAGEMENT → MEDICATION.
7. If uncertain between HEALTH and MEDICATION, choose HEALTH.
8. Never return anything except:
   MEDICATION
   HEALTH
   WEATHER
   GENERAL
   \
"""

# Health RAG
HEALTH_CORPUS_DIR = os.path.join(BASE_DIR, "data", "health_corpus")
HEALTH_INDEX_PATH = os.path.join(BASE_DIR, "data", "health_index.db")
HEALTH_EMBED_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
HEALTH_EMBED_DIM = 384
HEALTH_CHUNK_MAX_CHARS = 800
HEALTH_RETRIEVAL_K = 3
HEALTH_RETRIEVAL_MIN_SCORE = 0.35

# Flask web UI
FLASK_SECRET_KEY = os.getenv("FLASK_SECRET_KEY", "dev-insecure-change-me")
WEB_PASSWORD = os.getenv("WEB_PASSWORD", "aloxa")
WEB_HOST = os.getenv("WEB_HOST", "0.0.0.0")
WEB_PORT = int(os.getenv("WEB_PORT", "5000"))

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
