import re
from datetime import datetime, timedelta

from medication.manager import MedicationManager


def _parse_times(raw: str) -> list[str] | None:
    """Parse comma-separated HH:MM times. Returns None on validation error."""
    times = [t.strip() for t in raw.split(",") if t.strip()]
    for t in times:
        if not re.match(r"^\d{2}:\d{2}$", t):
            print(f"  Invalid time format: '{t}'. Use HH:MM.")
            return None
    if not times:
        print("  At least one scheduled time is required.")
        return None
    return times


def print_medications(manager: MedicationManager):
    print(f"  Current time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    meds = manager.get_all_medications()
    if not meds:
        print("  No medications registered.")
        return

    for container in ("A", "B"):
        print(f"\n  ┌─ Container {container} " + "─" * 40)
        in_container = [m for m in meds if m.container == container]
        if not in_container:
            print("  │  (empty)")
        else:
            for med in in_container:
                times = ", ".join(med.scheduled_times) or "none"
                info = f" ({med.information})" if med.information else ""
                print(f"  │  [{med.id}] {med.name} {med.dosage} — {times}{info}")
        print("  └" + "─" * 52)


def add_medication(manager: MedicationManager):
    name = input("  Name: ").strip()
    if not name:
        print("  Name cannot be empty.")
        return

    dosage = input("  Dosage: ").strip()
    if not dosage:
        print("  Dosage cannot be empty.")
        return

    information = input("  Info (optional): ").strip()

    raw_times = input("  Scheduled times (comma-separated, e.g. 08:00,22:00): ").strip()
    times = _parse_times(raw_times)
    if times is None:
        return

    container = input("  Container (A/B): ").strip().upper()
    if container not in ("A", "B"):
        print("  Container must be 'A' or 'B'.")
        return

    med_id = manager.add_medication(name, dosage, information, times, container)
    print(f"  Registered '{name}' (id={med_id})")


def update_medication(manager: MedicationManager):
    print_medications(manager)
    raw = input("  Enter medication ID to update: ").strip()
    if not raw.isdigit():
        print("  Invalid ID.")
        return

    med = manager.get_medication(int(raw))
    if not med:
        print(f"  Medication {raw} not found.")
        return

    print(f"  Updating [{med.id}] {med.name} {med.dosage} — {', '.join(med.scheduled_times)}")
    print("  Press Enter to keep current value.\n")

    name = input(f"  Name [{med.name}]: ").strip() or med.name
    dosage = input(f"  Dosage [{med.dosage}]: ").strip() or med.dosage
    information = input(f"  Info [{med.information or ''}]: ").strip() or med.information

    current_times = ", ".join(med.scheduled_times)
    raw_times = input(f"  Scheduled times [{current_times}]: ").strip()
    if raw_times:
        times = _parse_times(raw_times)
        if times is None:
            return
    else:
        times = med.scheduled_times

    manager.update_medication(med.id, name=name, dosage=dosage, information=information, times=times)
    print(f"  Updated '{name}' — {', '.join(times)}")


def respond_to_reminders(manager: MedicationManager):
    pending = manager.get_pending_reminders()
    if not pending:
        print("  No pending reminders.")
        return

    for r in pending:
        print(f"\n  [{r['id']}] {r['name']} {r['dosage']} — scheduled {r['scheduled_time']} (since {r['reminded_at']})")
        choice = input("  Mark as (t)aken, (m)issed, or (s)kip? ").strip().lower()
        if choice == "t":
            manager.mark_taken(r["id"])
            print(f"  Marked as taken.")
        elif choice == "m":
            manager.mark_missed(r["id"])
            print(f"  Marked as missed.")
        else:
            print(f"  Skipped.")


def view_intake_history(manager: MedicationManager):
    print_medications(manager)
    raw = input("  Enter medication ID (or Enter for all): ").strip()

    if raw and not raw.isdigit():
        print("  Invalid ID.")
        return

    if raw:
        history = manager.get_intake_history(int(raw))
    else:
        history = manager.get_all_intake_history()

    if not history:
        print("  No intake history.")
        return

    for entry in history:
        status = entry["status"].upper()
        responded = entry["responded_at"] or "—"
        print(f"  {entry['reminded_at']} | {entry['scheduled_time']} | {status} | responded: {responded}")


def delete_medication(manager: MedicationManager):
    print_medications(manager)
    raw = input("  Enter medication ID to delete: ").strip()
    if not raw.isdigit():
        print("  Invalid ID.")
        return

    med_id = int(raw)
    if manager.delete_medication(med_id):
        print(f"  Deleted medication {med_id}.")
    else:
        print(f"  Medication {med_id} not found.")


def load_mock_data(manager: MedicationManager):
    """Insert test medications with a reminder due right now to exercise repeat alerts."""
    manager.reset_all()

    now = datetime.now()
    # A time 2 minutes ago — triggers immediately and repeats every 5 min
    past_time = (now - timedelta(minutes=2)).strftime("%H:%M")
    # A time 30 minutes from now — won't fire yet
    future_time = (now + timedelta(minutes=30)).strftime("%H:%M")

    manager.add_medication("Paracetamol", "500mg", "Take with water", [past_time], container="A")
    manager.add_medication("Vitamin D", "1000 IU", "Take with food", [past_time, future_time], container="A")
    manager.add_medication("Ibuprofen", "200mg", "Take after meal", [past_time], container="B")
    manager.add_medication("Aspirin", "75mg", "Take with food", [future_time], container="B")

    print(f"  Mock data loaded.")
    print(f"  [A] Paracetamol  — due at {past_time} (should alert NOW and repeat every 5 min)")
    print(f"  [A] Vitamin D    — due at {past_time} (should alert NOW) + {future_time} (later)")
    print(f"  [B] Ibuprofen    — due at {past_time} (should alert NOW)")
    print(f"  [B] Aspirin      — due at {future_time} (not yet)")


def reset_all_data(manager: MedicationManager):
    confirm = input("  This will delete ALL medications and intake history. Type 'yes' to confirm: ").strip()
    if confirm == "yes":
        manager.reset_all()
        print("  All data has been reset.")
    else:
        print("  Cancelled.")
