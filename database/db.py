import os
import sqlite3

from config import DB_PATH


def get_connection() -> sqlite3.Connection:
    """Return a connection to the SQLite database, creating the data/ dir if needed."""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    """Create all tables from schema.sql if they don't already exist."""
    schema_path = os.path.join(os.path.dirname(__file__), "schema.sql")
    with open(schema_path) as f:
        schema = f.read()

    conn = get_connection()
    conn.executescript(schema)
    _migrate(conn)
    conn.close()


def _migrate(conn: sqlite3.Connection):
    """Add columns that may be missing from older databases."""
    columns = {r[1] for r in conn.execute("PRAGMA table_info(intake_log)").fetchall()}
    if "alert_count" not in columns:
        conn.execute("ALTER TABLE intake_log ADD COLUMN alert_count INTEGER NOT NULL DEFAULT 0")
    if "last_alerted_at" not in columns:
        conn.execute("ALTER TABLE intake_log ADD COLUMN last_alerted_at TIMESTAMP")

    med_columns = {r[1] for r in conn.execute("PRAGMA table_info(medications)").fetchall()}
    if "container" not in med_columns:
        # SQLite can't add a CHECK-constrained NOT NULL column via ALTER, so add
        # it with a default and rely on application-level validation.
        conn.execute("ALTER TABLE medications ADD COLUMN container TEXT NOT NULL DEFAULT 'A'")
    conn.commit()
