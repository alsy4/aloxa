import threading
import time
from datetime import datetime

from config import SCHEDULER_POLL_INTERVAL
from medication.manager import MedicationManager


class ReminderScheduler:

    def __init__(self, manager: MedicationManager):
        self.manager = manager
        self._running = False
        self._last_populated_date = None

    def start(self):
        self._running = True
        self._populate_today()
        t = threading.Thread(target=self._loop, daemon=True)
        t.start()
        print("[Scheduler] Started — monitoring reminder times.")

    def stop(self):
        self._running = False

    def _populate_today(self):
        """Create pending intake_log entries for all medications for today."""
        today = datetime.now().strftime("%Y-%m-%d")
        if self._last_populated_date != today:
            self.manager.populate_daily_reminders()
            self._last_populated_date = today

    def _loop(self):
        while self._running:
            try:
                self._populate_today()
                self.manager.expire_stale_reminders()
            except Exception as e:
                print(f"[Scheduler] Error: {e}")
            time.sleep(SCHEDULER_POLL_INTERVAL)
