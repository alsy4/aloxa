import atexit

from config import WEB_HOST, WEB_PORT
from database import init_db
from medication import MedicationManager
from medication.scheduler import ReminderScheduler, default_alert
from webapp import create_app
from webapp.broker import EventBroker


def main():
    init_db()
    manager = MedicationManager()
    broker = EventBroker()

    def alert_handler(reminder: dict, alert_count: int):
        default_alert(reminder, alert_count)
        broker.publish({
            "type": "reminder",
            "alert_count": alert_count,
            "reminder": {
                "id": reminder["id"],
                "name": reminder["name"],
                "dosage": reminder["dosage"],
                "scheduled_time": reminder["scheduled_time"],
            },
        })

    scheduler = ReminderScheduler(manager, on_alert=alert_handler)
    scheduler.start()
    atexit.register(scheduler.stop)

    app = create_app(manager, broker=broker)
    app.run(host=WEB_HOST, port=WEB_PORT, debug=False, use_reloader=False, threaded=True)


if __name__ == "__main__":
    main()
