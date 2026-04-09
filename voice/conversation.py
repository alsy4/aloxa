import re
from datetime import datetime

from llm.intent_classifier import classify_intent
from llm.ollama_client import OllamaClient
from medication.manager import MedicationManager
from voice.listener import SpeechListener


MEDICATION_CONTEXT_TEMPLATE = """\
TODAY: {today}

REGISTERED MEDICATIONS:
{medications}

TODAY'S INTAKE LOG:
{intake_log}

PENDING REMINDERS (not yet taken):
{pending}p

INSTRUCTIONS:
- When the user asks about their medications, reminders, or intake history, answer using the data above.
- When the user says they have taken a medication, identify which pending reminder \
it matches and include EXACTLY this tag in your response: [TAKEN: medication_name]
- The medication_name must match one of the registered medication names above exactly.
- If no pending reminders match, do NOT include the tag.
- Always respond naturally in addition to any tag."""


def _build_medication_context(manager: MedicationManager) -> str:
    """Build full medication context: all meds, today's log, and pending reminders."""
    today = datetime.now().strftime("%Y-%m-%d")

    # All registered medications
    meds = manager.get_all_medications()
    if meds:
        med_lines = []
        for m in meds:
            times = ", ".join(m.scheduled_times) or "no times set"
            info = f" — {m.information}" if m.information else ""
            med_lines.append(f"- {m.name} {m.dosage} at {times}{info}")
        medications_text = "\n".join(med_lines)
    else:
        medications_text = "(none registered)"

    # Today's intake history
    history = manager.get_all_intake_history()
    today_entries = [e for e in history if e["reminded_at"].startswith(today)]
    if today_entries:
        log_lines = []
        for e in today_entries:
            log_lines.append(
                f"- {e['name']} {e['dosage']} at {e['scheduled_time']}: {e['status'].upper()}"
            )
        intake_text = "\n".join(log_lines)
    else:
        intake_text = "(no entries today)"

    # Pending reminders
    pending = manager.get_pending_reminders()
    if pending:
        pending_lines = []
        for r in pending:
            pending_lines.append(
                f"- {r['name']} {r['dosage']} (scheduled {r['scheduled_time']})"
            )
        pending_text = "\n".join(pending_lines)
    else:
        pending_text = "(none — all taken or no reminders due)"

    return MEDICATION_CONTEXT_TEMPLATE.format(
        today=today,
        medications=medications_text,
        intake_log=intake_text,
        pending=pending_text,
    )


def _process_taken_tags(response: str, manager: MedicationManager) -> str:
    """Find [TAKEN: medication_name] tags in LLM response, mark matching reminders as taken.

    Returns the response with tags removed for clean display.
    """
    tags = re.findall(r"\[TAKEN:\s*(.+?)\]", response, re.IGNORECASE)
    if not tags:
        return response

    pending = manager.get_pending_reminders()

    for med_name in tags:
        med_name_lower = med_name.strip().lower()
        matched = [r for r in pending if r["name"].lower() == med_name_lower]
        if matched:
            for r in matched:
                manager.mark_taken(r["id"])
                print(f"  [Marked as taken: {r['name']} {r['dosage']} — {r['scheduled_time']}]")
        else:
            print(f"  [No pending reminder found for '{med_name}']")

    clean = re.sub(r"\s*\[TAKEN:\s*.+?\]", "", response).strip()
    return clean


def start_voice_conversation(manager: MedicationManager):
    """Voice conversation loop: speak → STT → Ollama (with medication context) → print response.

    Say "stop", "exit", or "quit" to end the conversation.
    """
    print("\n  Starting voice conversation with Aloxa...")
    print("  Say 'stop', 'exit', or 'quit' to end.\n")

    med_names = [m.name for m in manager.get_all_medications()]
    listener = SpeechListener(medication_names=med_names)
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

            intent = classify_intent(text)
            print(f"  [Intent: {intent}]")

            if intent == "HEALTH":
                print("  [Routing to Watson API]")
                reply = "This is a health-related query. Routing to Watson API..."
            elif intent == "WEATHER":
                print("  [Routing to Weather API]")
                reply = "This is a weather-related query. Routing to Weather API..."
            elif intent == "MEDICATION":
                print("  Aloxa is thinking...")
                context = _build_medication_context(manager)
                reply = client.chat(text, extra_context=context)
                reply = _process_taken_tags(reply, manager)
            else:
                print("  Aloxa is thinking...")
                reply = client.chat(text)

            print(f"  Aloxa: {reply}\n")
    except KeyboardInterrupt:
        print("\n  Conversation ended.")
    finally:
        listener.close()
