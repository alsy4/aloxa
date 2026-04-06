from llm.ollama_client import OllamaClient
from voice.listener import SpeechListener


def start_voice_conversation():
    """Voice conversation loop: speak → STT → Ollama → print response.

    Say "stop", "exit", or "quit" to end the conversation.
    """
    print("\n  Starting voice conversation with Aloxa...")
    print("  Say 'stop', 'exit', or 'quit' to end.\n")

    listener = SpeechListener()
    client = OllamaClient()

    exit_words = {"stop", "exit", "quit", "bye", "goodbye"}

    try:
        while True:
            text = listener.listen()
            if not text:
                continue

            print(f"  You: {text}")

            if text.strip().lower() in exit_words:
                print("  Aloxa: Goodbye!")
                break

            print("  Aloxa is thinking...")
            reply = client.chat(text)
            print(f"  Aloxa: {reply}\n")
    except KeyboardInterrupt:
        print("\n  Conversation ended.")
    finally:
        listener.close()
