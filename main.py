from database import init_db
from medication import MedicationManager
from medication.cli import (
    add_medication,
    delete_medication,
    print_medications,
    update_medication,
)


def main():
    init_db()
    manager = MedicationManager()

    while True:
        print("\n=== Aloxa Medication Manager ===")
        print("  1. View medications")
        print("  2. Add medication")
        print("  3. Update medication")
        print("  4. Delete medication")
        print("  5. Exit")

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
            print("Bye.")
            break
        else:
            print("Invalid choice.")


if __name__ == "__main__":
    main()
