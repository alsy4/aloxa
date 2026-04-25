"""Deterministic parser for spoken intake reports.

Recognises phrases like "I took my aspirin" and updates intake_log without
needing the LLM to emit a structured tag. The 0.5B Ollama model is too small
to reliably follow tag-emission instructions across a long context, so this
parser is the primary path for intake logging; the LLM tag fallback in
voice/conversation.py remains as a safety net for missed phrasings.
"""

from __future__ import annotations

import re
from datetime import datetime
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from medication.manager import MedicationManager


_INTAKE_VERB_RE = re.compile(
    r"\b(took|taken|swallowed|popped|had)\b",
    re.IGNORECASE,
)

_NEGATION_RE = re.compile(
    r"\b("
    r"haven['’]?t|hasn['’]?t|have\s+not|has\s+not|"
    r"did\s+not|didn['’]?t|don['’]?t|doesn['’]?t|"
    r"not\s+yet|won['’]?t|will\s+not|"
    r"forgot|forgotten|missed|skip|skipped"
    r")\b",
    re.IGNORECASE,
)


def parse_intake_report(
    text: str,
    manager: "MedicationManager",
) -> list[dict]:
    """Detect intake reports and mark matching reminders as taken.

    Returns a list of dicts describing what was logged:
        {name, dosage, scheduled_time, was_pending}
    Returns [] when the message is not an intake report.

    Behaviour:
    - Skipped if the text contains a negation ("haven't", "didn't", "not yet").
    - Requires an intake verb (took/taken/swallowed/popped/had).
    - Matches one or more registered medication names by word boundary.
    - For each matched med, marks the earliest pending reminder for today
      as taken. If no pending reminder exists, creates a one-off log entry
      at the current time and marks it taken so the intake is still recorded.
    """
    if _NEGATION_RE.search(text):
        return []
    if not _INTAKE_VERB_RE.search(text):
        return []

    meds = manager.get_all_medications()
    if not meds:
        return []

    text_lower = text.lower()
    matched = []
    for m in meds:
        name = (m.name or "").strip().lower()
        if not name:
            continue
        if re.search(r"\b" + re.escape(name) + r"\b", text_lower):
            matched.append(m)

    if not matched:
        return []

    pending = manager.get_pending_reminders()
    pending_by_med: dict[int, list[dict]] = {}
    for r in pending:
        pending_by_med.setdefault(r["medication_id"], []).append(r)

    logged: list[dict] = []
    for m in matched:
        candidates = sorted(
            pending_by_med.get(m.id, []),
            key=lambda r: r["scheduled_time"],
        )
        if candidates:
            r = candidates[0]
            manager.mark_taken(r["id"])
            logged.append({
                "name": m.name,
                "dosage": m.dosage,
                "scheduled_time": r["scheduled_time"],
                "was_pending": True,
            })
            # remove so a second matched mention doesn't double-mark
            pending_by_med[m.id] = candidates[1:]
        else:
            now_time = datetime.now().strftime("%H:%M")
            log_id = manager.log_reminder(m.id, now_time)
            manager.mark_taken(log_id)
            logged.append({
                "name": m.name,
                "dosage": m.dosage,
                "scheduled_time": now_time,
                "was_pending": False,
            })

    return logged


def format_intake_reply(entries: list[dict]) -> str:
    """Build a short spoken acknowledgment for parsed intake entries."""
    if not entries:
        return ""

    if len(entries) == 1:
        e = entries[0]
        if e["was_pending"]:
            return (
                f"Got it — I've marked your {e['name']} {e['dosage']} "
                f"from {e['scheduled_time']} as taken."
            )
        return (
            f"Got it — I've logged your {e['name']} {e['dosage']} as taken, "
            "though it wasn't on your schedule for now."
        )

    parts = [f"{e['name']} {e['dosage']}" for e in entries]
    joined = ", ".join(parts[:-1]) + f" and {parts[-1]}"
    return f"Got it — I've logged {joined} as taken."
