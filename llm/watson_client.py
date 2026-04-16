from ibm_watsonx_ai.credentials import Credentials
from ibm_watsonx_ai.foundation_models.inference import ModelInference

from config import (
    WATSONX_API_KEY,
    WATSONX_HEALTH_SYSTEM_PROMPT,
    WATSONX_MODEL,
    WATSONX_PROJECT_ID,
    WATSONX_URL,
)


class WatsonHealthClient:
    """WatsonX client for health-related queries using IBM Granite."""

    def __init__(self):
        credentials = Credentials(api_key=WATSONX_API_KEY, url=WATSONX_URL)
        self.model = ModelInference(
            model_id=WATSONX_MODEL,
            credentials=credentials,
            project_id=WATSONX_PROJECT_ID,
        )
        self.system_prompt = WATSONX_HEALTH_SYSTEM_PROMPT

    def ask(self, user_message: str, medication_context: str = "") -> str:
        """Send a health query to WatsonX and return the response.

        medication_context: current medication info (names, dosages) for grounding.
        """
        system = self.system_prompt
        if medication_context:
            system = f"{system}\n\nUSER'S CURRENT MEDICATIONS:\n{medication_context}"

        messages = [
            {"role": "system", "content": system},
            {"role": "user", "content": user_message},
        ]

        try:
            response = self.model.chat(
                messages=messages,
                params={"max_tokens": 256, "temperature": 0.7},
            )
            return response["choices"][0]["message"]["content"]
        except Exception as e:
            return f"Sorry, I couldn't reach my health knowledge service. Please check with your doctor. Error: {e}"
