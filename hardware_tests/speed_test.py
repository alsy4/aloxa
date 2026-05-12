import ollama
import time

# Golden dataset: each entry has a prompt, expected keywords that a correct
# response should contain, and the intent category for classification accuracy.
test_dataset = [
    {
        "prompt": "What time should I take my 50mg Sertraline?",
        "expected_keywords": ["sertraline", "50mg"],
        "intent": "medication_query",
    },
    {
        "prompt": "Can I take Ibuprofen with my blood pressure medication?",
        "expected_keywords": ["ibuprofen", "blood pressure"],
        "intent": "health_query",
    },
    {
        "prompt": "Set a reminder for my heart pill at 9 PM.",
        "expected_keywords": ["reminder", "9"],
        "intent": "medication_confirm",
    },
    {
        "prompt": "What's the weather like today?",
        "expected_keywords": ["weather"],
        "intent": "weather_query",
    },
    {
        "prompt": "Did I take my medication this morning?",
        "expected_keywords": ["medication", "morning"],
        "intent": "medication_query",
    },
]

GENERATION_SYSTEM_PROMPT = (
    "You are Aloxa, a helpful medication reminder assistant. "
    "You help users manage their medications, answer health-related questions, "
    "and provide useful information. Be concise and helpful."
)

INTENT_SYSTEM_PROMPT = (
    "You are an intent classifier for a medication reminder assistant. "
    "Classify the user message into exactly one of these intents: "
    "medication_query, medication_confirm, health_query, weather_query, general. "
    "Reply with ONLY the intent label, nothing else."
)

# models = ["qwen2.5:7b", "deepseek-r1:8b", "gemma2:2b", "granite3.1-dense:8b"]
models = ["qwen2.5:0.5b", "qwen2.5:1.5b"]


def run_generation_test(model_name, prompt):
    """Test response generation speed and quality."""
    start = time.time()
    response = ollama.chat(
        model=model_name,
        messages=[
            {"role": "system", "content": GENERATION_SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
    )
    end = time.time()

    wall_time = end - start
    tokens = response.get("eval_count", 0)
    eval_duration = response.get("eval_duration", 1)
    tps = tokens / eval_duration * 1e9 if eval_duration else 0
    ttft = response.get("total_duration", 0) / 1e9

    return {
        "wall_time": wall_time,
        "ttft": ttft,
        "tps": tps,
        "tokens": tokens,
        "text": response["message"]["content"],
    }


def run_intent_test(model_name, prompt):
    """Test intent classification accuracy with clean role separation."""
    response = ollama.chat(
        model=model_name,
        messages=[
            # The system role sets the behavior
            {"role": "system", "content": INTENT_SYSTEM_PROMPT},
            # The user role provides ONLY the input
            {"role": "user", "content": prompt},
        ],
        options={
            "temperature": 0,      # Make it deterministic
            "num_predict": 10      # Stop it from yapping after the label
        }
    )
    return response["message"]["content"].strip().lower()


def check_keyword_accuracy(response_text, expected_keywords):
    """Check how many expected keywords appear in the response."""
    text_lower = response_text.lower()
    hits = sum(1 for kw in expected_keywords if kw.lower() in text_lower)
    return hits / len(expected_keywords) if expected_keywords else 1.0


def print_separator():
    print("=" * 90)


def main():
    for model in models:
        print_separator()
        print(f"MODEL: {model}")
        print_separator()

        total_tps = 0 # Tokens per second
        total_ttft = 0 # Time to first token
        total_keyword_acc = 0
        intent_correct = 0

        for i, entry in enumerate(test_dataset, 1):
            prompt = entry["prompt"]
            print(f"\n  [{i}] {prompt}")

            # Generation test
            result = run_generation_test(model, prompt)
            keyword_acc = check_keyword_accuracy(result["text"], entry["expected_keywords"])

            print(f"      TPS: {result['tps']:.1f} | TTFT: {result['ttft']:.2f}s | "
                  f"Tokens: {result['tokens']} | Wall: {result['wall_time']:.2f}s")
            print(f"      Keyword accuracy: {keyword_acc:.0%}")
            print(f"      Response: {result['text'][:150]}...")

            # Intent classification test
            predicted_intent = run_intent_test(model, prompt)
            intent_match = entry["intent"] in predicted_intent
            intent_correct += int(intent_match)
            mark = "OK" if intent_match else "MISS"
            print(f"      Intent: expected={entry['intent']} got={predicted_intent} [{mark}]")

            total_tps += result["tps"]
            total_ttft += result["ttft"]
            total_keyword_acc += keyword_acc

        n = len(test_dataset)
        print(f"\n  --- {model} Summary ---")
        print(f"  Avg TPS:              {total_tps / n:.1f}")
        print(f"  Avg TTFT:             {total_ttft / n:.2f}s")
        print(f"  Avg keyword accuracy: {total_keyword_acc / n:.0%}")
        print(f"  Intent accuracy:      {intent_correct}/{n} ({intent_correct / n:.0%})")
        print()

    print_separator()
    print("Done.")


if __name__ == "__main__":
    main()
