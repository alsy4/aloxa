import threading
import time
from datetime import datetime

from config import SCHEDULER_POLL_INTERVAL
from medication.manager import MedicationManager


class ReminderScheduler:

    def __init__(self, manager: MedicationManager):
        self.manager = manager
        self._running = False

    def start(self):
        self._running = True
        t = threading.Thread(target=self._loop, daemon=True)
        t.start()
        print("[Scheduler] Started — monitoring reminder times.")

    def stop(self):
        self._running = False

    def _loop(self):
        while self._running:
            try:
                self._check()
            except Exception as e:
                print(f"[Scheduler] Error: {e}")
            time.sleep(SCHEDULER_POLL_INTERVAL)

    def _check(self):
        now = datetime.now().strftime("%H:%M")

        # Expire any reminders that have been pending longer than the timeout
        self.manager.expire_stale_reminders()

        # Check each medication's scheduled times against current time
        for med in self.manager.get_all_medications():
            for scheduled_time in med.scheduled_times:
                if scheduled_time == now and not self.manager.has_reminder_today(med.id, scheduled_time):
                    log_id = self.manager.log_reminder(med.id, scheduled_time)
                    print(f"\n[Reminder] Time to take {med.name} {med.dosage}! (log_id={log_id})")
