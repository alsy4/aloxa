import os
import sys

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


@pytest.fixture
def manager(tmp_path, monkeypatch):
    """Fresh MedicationManager backed by an isolated temp SQLite DB."""
    db_file = tmp_path / "aloxa_test.db"

    import config
    monkeypatch.setattr(config, "DB_PATH", str(db_file))

    import database.db as db_module
    monkeypatch.setattr(db_module, "DB_PATH", str(db_file))

    from database.db import init_db
    init_db()

    from medication.manager import MedicationManager
    return MedicationManager()
