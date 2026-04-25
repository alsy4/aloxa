from ibm_watsonx_ai.credentials import Credentials
from ibm_watsonx_ai.foundation_models.inference import ModelInference

from config import (
    WATSONX_API_KEY,
    WATSONX_HEALTH_SYSTEM_PROMPT,
    WATSONX_MODEL,
    WATSONX_PROJECT_ID,
    WATSONX_URL,
)
from llm.health_retriever import HealthRetriever, RetrievedChunk


class WatsonHealthClient:
    """WatsonX client for health-related queries, grounded in NHS passages."""

    def __init__(self):
        credentials = Credentials(api_key=WATSONX_API_KEY, url=WATSONX_URL)
        self.model = ModelInference(
            model_id=WATSONX_MODEL,
            credentials=credentials,
            project_id=WATSONX_PROJECT_ID,
        )
        self.system_prompt = WATSONX_HEALTH_SYSTEM_PROMPT

        try:
            self.retriever: HealthRetriever | None = HealthRetriever()
        except FileNotFoundError as e:
            print(f"  [WatsonX] Retriever disabled: {e}")
            self.retriever = None

    def ask(self, user_message: str, medication_context: str = "") -> str:
        """Send a health query to WatsonX and return the response.

        medication_context: current medication info (names, dosages) for grounding.
        """
        system = self.system_prompt
        if medication_context:
            system = f"{system}\n\nUSER'S CURRENT MEDICATIONS:\n{medication_context}"

        passages: list[RetrievedChunk] = []
        if self.retriever is not None:
            passages = self.retriever.retrieve(user_message)

        if passages:
            refs = "\n\n".join(
                f"[{p.title}{' — ' + p.section if p.section else ''}]\n{p.text}"
                for p in passages
            )
            system = (
                f"{system}\n\n"
                "REFERENCE INFORMATION (use only these facts):\n"
                f"{refs}"
            )
            print(f"  [WatsonX] Grounded with {len(passages)} NHS passage(s)")
        else:
            print("  [WatsonX] No reference passages retrieved")

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
