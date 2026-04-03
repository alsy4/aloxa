import re

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
    meds = manager.get_all_medications()
    if not meds:
        print("  No medications registered.")
        return
    for med in meds:
        times = ", ".join(med.scheduled_times) or "none"
        info = f" ({med.information})" if med.information else ""
        print(f"  [{med.id}] {med.name} {med.dosage} — {times}{info}")


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

    med_id = manager.add_medication(name, dosage, information, times)
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
