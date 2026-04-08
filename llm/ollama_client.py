import requests

from config import OLLAMA_BASE_URL, OLLAMA_MODEL, OLLAMA_SYSTEM_PROMPT


class OllamaClient:
    """Stateful chat client for a local Ollama model with conversation history."""

    def __init__(self, model: str = OLLAMA_MODEL, system_prompt: str = OLLAMA_SYSTEM_PROMPT):
        self.model = model
        self.system_prompt = system_prompt
        self.history: list[dict] = []

    def chat(self, user_message: str, extra_context: str = "") -> str:
        """Send a message and return the assistant's reply. Maintains conversation history.

        extra_context is appended to the system prompt for this turn only (e.g. pending reminders).
        """
        self.history.append({"role": "user", "content": user_message})

        system = self.system_prompt
        if extra_context:
            system = f"{system}\n\n{extra_context}"

        messages = [{"role": "system", "content": system}] + self.history

        try:
            resp = requests.post(
                f"{OLLAMA_BASE_URL}/api/chat",
                json={"model": self.model, "messages": messages, "stream": False},
                timeout=60,
            )
            resp.raise_for_status()
            reply = resp.json()["message"]["content"]
        except requests.ConnectionError:
            reply = "Sorry, I can't reach the language model. Is Ollama running?"
            self.history.pop()
            return reply
        except (requests.RequestException, KeyError) as e:
            reply = f"LLM error: {e}"
            self.history.pop()
            return reply

        self.history.append({"role": "assistant", "content": reply})
        return reply

    def clear_history(self):
        self.history.clear()
