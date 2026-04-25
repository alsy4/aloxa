import requests

from config import CLASSIFY_PROMPT, MEDICATION_KEYWORDS, OLLAMA_BASE_URL, OLLAMA_MODEL


def _keyword_match(text: str) -> bool:
    """Check if text contains unambiguous CRUD / intake-log phrases.

    Drug-name mentions are NOT matched here — a user naming their medication
    could be asking a HEALTH question ("what are the side effects of my
    ramipril?"), so that judgment is delegated to the LLM.
    """
    text_lower = text.lower()
    for kw in MEDICATION_KEYWORDS:
        if kw in text_lower:
            return True
    return False


def classify_intent(
    user_message: str,
    medication_names: list[str] | None = None,
) -> str:
    """Classify user message into an intent category.

    Uses keyword pre-filtering for clear CRUD/intake phrases, then falls back
    to Ollama. medication_names is passed to the LLM only as recognition
    context — it does not force a MEDICATION classification.

    Returns one of: MEDICATION, HEALTH, WEATHER, GENERAL.
    """
    # Keyword pre-filter — deterministic and instant for obvious CRUD phrases
    if _keyword_match(user_message):
        return "MEDICATION"

    # Provide the user's medication names as context so the LLM can recognise
    # them, but let the prompt's rules decide the intent (HEALTH vs MEDICATION).
    prompt = CLASSIFY_PROMPT
    if medication_names:
        names_str = ", ".join(medication_names)
        prompt += (
            f"\n\nContext: the user's registered medications are: {names_str}. "
            "Use this only to recognise these drug names; it does not "
            "determine the label — apply the rules and examples above."
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
