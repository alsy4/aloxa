import re

from database import init_db
from medication import MedicationManager


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
    times = [t.strip() for t in raw_times.split(",") if t.strip()]
    for t in times:
        if not re.match(r"^\d{2}:\d{2}$", t):
            print(f"  Invalid time format: '{t}'. Use HH:MM.")
            return

    if not times:
        print("  At least one scheduled time is required.")
        return

    med_id = manager.add_medication(name, dosage, information, times)
    print(f"  Registered '{name}' (id={med_id})")


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


def main():
    init_db()
    manager = MedicationManager()

    while True:
        print("\n=== Aloxa Medication Manager ===")
        print("  1. View medications")
        print("  2. Add medication")
        print("  3. Delete medication")
        print("  4. Exit")

        choice = input("Select: ").strip()

        if choice == "1":
            print_medications(manager)
        elif choice == "2":
            add_medication(manager)
        elif choice == "3":
            delete_medication(manager)
        elif choice == "4":
            print("Bye.")
            break
        else:
            print("Invalid choice.")


if __name__ == "__main__":
    main()
