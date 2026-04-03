from datetime import datetime, timedelta

from config import MISSED_TIMEOUT_SECONDS
from database import get_connection
from medication.models import Medication


class MedicationManager:

    # ── CRUD ────────────────────────────────────────────────

    def add_medication(self, name: str, dosage: str, information: str,
                       times: list[str]) -> int:
        """Register a medication with one or more scheduled times (HH:MM)."""
        conn = get_connection()
        cursor = conn.execute(
            "INSERT INTO medications (name, dosage, information) VALUES (?, ?, ?)",
            (name, dosage, information),
        )
        med_id = cursor.lastrowid
        for t in times:
            conn.execute(
                "INSERT INTO medication_times (medication_id, scheduled_time) VALUES (?, ?)",
                (med_id, t),
            )
        conn.commit()
        conn.close()
        return med_id

    def get_all_medications(self) -> list[Medication]:
        conn = get_connection()
        rows = conn.execute("SELECT * FROM medications").fetchall()
        meds = []
        for row in rows:
            times = conn.execute(
                "SELECT scheduled_time FROM medication_times WHERE medication_id = ?",
                (row["id"],),
            ).fetchall()
            meds.append(Medication(
                id=row["id"],
                name=row["name"],
                dosage=row["dosage"],
                information=row["information"],
                scheduled_times=[t["scheduled_time"] for t in times],
            ))
        conn.close()
        return meds

    def get_medication(self, med_id: int) -> Medication | None:
        conn = get_connection()
        row = conn.execute(
            "SELECT * FROM medications WHERE id = ?", (med_id,)
        ).fetchone()
        if not row:
            conn.close()
            return None
        times = conn.execute(
            "SELECT scheduled_time FROM medication_times WHERE medication_id = ?",
            (med_id,),
        ).fetchall()
        conn.close()
        return Medication(
            id=row["id"],
            name=row["name"],
            dosage=row["dosage"],
            information=row["information"],
            scheduled_times=[t["scheduled_time"] for t in times],
        )

    def update_medication(self, med_id: int, **fields) -> bool:
        """Update medication fields. Pass times=["HH:MM",...] to replace scheduled times."""
        conn = get_connection()
        # Update core fields
        allowed = {"name", "dosage", "information"}
        updates = {k: v for k, v in fields.items() if k in allowed}
        if updates:
            set_clause = ", ".join(f"{k} = ?" for k in updates)
            conn.execute(
                f"UPDATE medications SET {set_clause} WHERE id = ?",
                (*updates.values(), med_id),
            )
        # Replace scheduled times if provided
        if "times" in fields:
            conn.execute(
                "DELETE FROM medication_times WHERE medication_id = ?", (med_id,)
            )
            for t in fields["times"]:
                conn.execute(
                    "INSERT INTO medication_times (medication_id, scheduled_time) VALUES (?, ?)",
                    (med_id, t),
                )
        conn.commit()
        conn.close()
        return True

    def delete_medication(self, med_id: int) -> bool:
        conn = get_connection()
        cursor = conn.execute("DELETE FROM medications WHERE id = ?", (med_id,))
        conn.commit()
        conn.close()
        return cursor.rowcount > 0

    # ── Intake logging ──────────────────────────────────────

    def log_reminder(self, medication_id: int, scheduled_time: str) -> int:
        """Create a pending intake log entry when a reminder fires."""
        conn = get_connection()
        cursor = conn.execute(
            "INSERT INTO intake_log (medication_id, scheduled_time, status) VALUES (?, ?, 'pending')",
            (medication_id, scheduled_time),
        )
        conn.commit()
        log_id = cursor.lastrowid
        conn.close()
        return log_id

    def mark_taken(self, log_id: int):
        """Mark a pending reminder as taken."""
        conn = get_connection()
        conn.execute(
            "UPDATE intake_log SET status = 'taken', responded_at = CURRENT_TIMESTAMP WHERE id = ?",
            (log_id,),
        )
        conn.commit()
        conn.close()

    def mark_missed(self, log_id: int):
        """Mark a pending reminder as missed."""
        conn = get_connection()
        conn.execute(
            "UPDATE intake_log SET status = 'missed', responded_at = CURRENT_TIMESTAMP WHERE id = ?",
            (log_id,),
        )
        conn.commit()
        conn.close()

    def expire_stale_reminders(self):
        """Mark all pending reminders older than MISSED_TIMEOUT_SECONDS as missed."""
        cutoff = datetime.now() - timedelta(seconds=MISSED_TIMEOUT_SECONDS)
        conn = get_connection()
        conn.execute(
            "UPDATE intake_log SET status = 'missed', responded_at = CURRENT_TIMESTAMP "
            "WHERE status = 'pending' AND reminded_at <= ?",
            (cutoff.strftime("%Y-%m-%d %H:%M:%S"),),
        )
        conn.commit()
        conn.close()

    def get_intake_history(self, medication_id: int, date: str | None = None) -> list[dict]:
        """Return intake log entries. If date given (YYYY-MM-DD), filter to that day."""
        conn = get_connection()
        if date:
            rows = conn.execute(
                "SELECT * FROM intake_log WHERE medication_id = ? AND DATE(reminded_at) = ? ORDER BY reminded_at",
                (medication_id, date),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM intake_log WHERE medication_id = ? ORDER BY reminded_at",
                (medication_id,),
            ).fetchall()
        conn.close()
        return [dict(r) for r in rows]

    def has_reminder_today(self, medication_id: int, scheduled_time: str) -> bool:
        """Check if a reminder was already logged today for this medication+time."""
        today = datetime.now().strftime("%Y-%m-%d")
        conn = get_connection()
        row = conn.execute(
            "SELECT id FROM intake_log "
            "WHERE medication_id = ? AND scheduled_time = ? AND DATE(reminded_at) = ?",
            (medication_id, scheduled_time, today),
        ).fetchone()
        conn.close()
        return row is not None

    def get_all_intake_history(self) -> list[dict]:
        """Return all intake log entries across all medications."""
        conn = get_connection()
        rows = conn.execute(
            "SELECT il.*, m.name, m.dosage FROM intake_log il "
            "JOIN medications m ON il.medication_id = m.id "
            "ORDER BY il.reminded_at DESC",
        ).fetchall()
        conn.close()
        return [dict(r) for r in rows]

    def get_pending_reminders(self) -> list[dict]:
        """Return all currently pending intake log entries."""
        conn = get_connection()
        rows = conn.execute(
            "SELECT il.*, m.name, m.dosage FROM intake_log il "
            "JOIN medications m ON il.medication_id = m.id "
            "WHERE il.status = 'pending' ORDER BY il.reminded_at",
        ).fetchall()
        conn.close()
        return [dict(r) for r in rows]
