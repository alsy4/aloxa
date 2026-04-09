import re

import requests

from config import OLLAMA_BASE_URL, OLLAMA_MODEL

# Keyword triggers that always classify as MEDICATION without hitting the LLM
_MEDICATION_KEYWORDS = {
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


def _keyword_match(text: str, medication_names: list[str] | None = None) -> bool:
    """Check if text contains medication keywords or known medication names."""
    text_lower = text.lower()

    # Check keyword phrases (multi-word first)
    for kw in _MEDICATION_KEYWORDS:
        if kw in text_lower:
            return True

    # Check registered medication names from the database
    if medication_names:
        for name in medication_names:
            if name.lower() in text_lower:
                return True

    return False


def classify_intent(
    user_message: str,
    medication_names: list[str] | None = None,
) -> str:
    """Classify user message into an intent category.

    Uses keyword pre-filtering for medication queries, then falls back to Ollama.
    medication_names: list of registered medication names from the DB for matching.

    Returns one of: MEDICATION, HEALTH, WEATHER, GENERAL.
    """
    # Option 1: Keyword pre-filter — deterministic and instant
    if _keyword_match(user_message, medication_names):
        return "MEDICATION"

    # Option 3: Inject medication names into the prompt so the LLM recognises them
    prompt = CLASSIFY_PROMPT
    if medication_names:
        names_str = ", ".join(medication_names)
        prompt += (
            f"\n\nThe user has these registered medications: {names_str}. "
            "If the message refers to any of these, classify as MEDICATION."
        )

    # Option 2: temperature 0 for deterministic output
    try:
        resp = requests.post(
            f"{OLLAMA_BASE_URL}/api/chat",
            json={
                "model": OLLAMA_MODEL,
                "messages": [
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": user_message},
                ],
                "stream": False,
                "options": {"temperature": 0},
            },
            timeout=30,
        )
        resp.raise_for_status()
        label = resp.json()["message"]["content"].strip().upper()
    except (requests.RequestException, KeyError):
        return "GENERAL"

    valid = {"MEDICATION", "HEALTH", "WEATHER", "GENERAL"}
    # Handle cases where the model returns extra text around the label
    for v in valid:
        if v in label:
            return v
    return "GENERAL"
