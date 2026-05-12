import threading
import time
from datetime import datetime

import medication.compartment_leds as compartment_leds
import medication.compartment_servos as compartment_servos
from config import SCHEDULER_POLL_INTERVAL
from medication.manager import MedicationManager


def default_alert(reminder: dict, alert_count: int):
    """Console alert — will be replaced by hardware alerts later."""
    ordinal = "INITIAL" if alert_count == 1 else f"REPEAT #{alert_count - 1}"
    print(
        f"\n  [ALERT — {ordinal}] "
        f"Time to take {reminder['name']} {reminder['dosage']} "
        f"(scheduled {reminder['scheduled_time']})"
    )


class ReminderScheduler:

    def __init__(self, manager: MedicationManager, on_alert=None):
        self.manager = manager
        self.on_alert = on_alert or default_alert
        self._running = False
        self._last_populated_date = None

    def start(self):
        self._running = True
        self._populate_today()
        compartment_leds.refresh()
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

    def _check_alerts(self):
        """Fire alerts for pending reminders that are due (initial or repeat)."""
        due = self.manager.get_due_alerts()
        for reminder in due:
            self.manager.record_alert(reminder["id"])
            alert_count = reminder["alert_count"] + 1
            self.on_alert(reminder, alert_count)
            compartment_servos.rotate()

    def _loop(self):
        while self._running:
            try:
                self._populate_today()
                self._check_alerts()
                self.manager.expire_stale_reminders()
            except Exception as e:
                print(f"[Scheduler] Error: {e}")
            time.sleep(SCHEDULER_POLL_INTERVAL)
