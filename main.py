from database import init_db
from medication import MedicationManager
from medication.cli import (
    add_medication,
    delete_medication,
    print_medications,
    respond_to_reminders,
    update_medication,
    view_intake_history,
)
from medication.scheduler import ReminderScheduler


def main():
    init_db()
    manager = MedicationManager()

    scheduler = ReminderScheduler(manager)
    scheduler.start()

    while True:
        print("\n=== Aloxa Medication Manager ===")
        print("  1. View medications")
        print("  2. Add medication")
        print("  3. Update medication")
        print("  4. Delete medication")
        print("  5. Respond to reminders")
        print("  6. Intake history")
        print("  7. Exit")

        choice = input("Select: ").strip()

        if choice == "1":
            print_medications(manager)
        elif choice == "2":
            add_medication(manager)
        elif choice == "3":
            update_medication(manager)
        elif choice == "4":
            delete_medication(manager)
        elif choice == "5":
            respond_to_reminders(manager)
        elif choice == "6":
            view_intake_history(manager)
        elif choice == "7":
            scheduler.stop()
            print("Bye.")
            break
        else:
            print("Invalid choice.")


if __name__ == "__main__":
    main()
