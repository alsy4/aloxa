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
    conn.close()
