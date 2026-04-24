import requests

from config import CLASSIFY_PROMPT, MEDICATION_KEYWORDS, OLLAMA_BASE_URL, OLLAMA_MODEL


def _keyword_match(text: str, medication_names: list[str] | None = None) -> bool:
    """Check if text contains medication keywords or known medication names."""
    text_lower = text.lower()

    # Check keyword phrases (multi-word first)
    for kw in MEDICATION_KEYWORDS:
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
