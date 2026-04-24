import pytest

from medication.models import Medication


# ── Create ──────────────────────────────────────────────

def test_add_medication_returns_id(manager):
    med_id = manager.add_medication("Aspirin", "100mg", "After food", ["08:00"])
    assert isinstance(med_id, int) and med_id > 0


def test_add_medication_persists_fields(manager):
    med_id = manager.add_medication("Aspirin", "100mg", "After food", ["08:00"])
    med = manager.get_medication(med_id)
    assert med.name == "Aspirin"
    assert med.dosage == "100mg"
    assert med.information == "After food"
    assert med.scheduled_times == ["08:00"]


def test_add_medication_with_multiple_times(manager):
    med_id = manager.add_medication("Metformin", "500mg", "", ["08:00", "14:00", "22:00"])
    med = manager.get_medication(med_id)
    assert sorted(med.scheduled_times) == ["08:00", "14:00", "22:00"]


def test_add_medication_with_no_times(manager):
    med_id = manager.add_medication("PRN Painkiller", "200mg", "As needed", [])
    med = manager.get_medication(med_id)
    assert med.scheduled_times == []


def test_add_medication_allows_duplicate_names(manager):
    id1 = manager.add_medication("Aspirin", "100mg", "", ["08:00"])
    id2 = manager.add_medication("Aspirin", "300mg", "", ["09:00"])
    assert id1 != id2
    assert len(manager.get_all_medications()) == 2


# ── Read ────────────────────────────────────────────────

def test_get_medication_missing_returns_none(manager):
    assert manager.get_medication(9999) is None


def test_get_medication_returns_medication_instance(manager):
    med_id = manager.add_medication("Aspirin", "100mg", "", ["08:00"])
    med = manager.get_medication(med_id)
    assert isinstance(med, Medication)
    assert med.id == med_id


def test_get_all_medications_empty(manager):
    assert manager.get_all_medications() == []


def test_get_all_medications_returns_all(manager):
    manager.add_medication("A", "1mg", "", ["08:00"])
    manager.add_medication("B", "2mg", "", ["09:00"])
    manager.add_medication("C", "3mg", "", ["10:00"])
    meds = manager.get_all_medications()
    assert {m.name for m in meds} == {"A", "B", "C"}


# ── Update ──────────────────────────────────────────────

def test_update_medication_name(manager):
    med_id = manager.add_medication("Aspirin", "100mg", "", ["08:00"])
    manager.update_medication(med_id, name="Aspirin EC")
    assert manager.get_medication(med_id).name == "Aspirin EC"


def test_update_medication_multiple_fields(manager):
    med_id = manager.add_medication("Aspirin", "100mg", "old", ["08:00"])
    manager.update_medication(med_id, dosage="200mg", information="new")
    med = manager.get_medication(med_id)
    assert med.dosage == "200mg"
    assert med.information == "new"
    assert med.name == "Aspirin"  # untouched


def test_update_medication_ignores_unknown_fields(manager):
    med_id = manager.add_medication("Aspirin", "100mg", "", ["08:00"])
    # Should not raise, should not change anything
    manager.update_medication(med_id, bogus_field="x", another="y")
    med = manager.get_medication(med_id)
    assert med.name == "Aspirin"


def test_update_medication_replaces_times(manager):
    med_id = manager.add_medication("Aspirin", "100mg", "", ["08:00", "20:00"])
    manager.update_medication(med_id, times=["09:00"])
    assert manager.get_medication(med_id).scheduled_times == ["09:00"]


def test_update_medication_empty_times_clears_schedule(manager):
    med_id = manager.add_medication("Aspirin", "100mg", "", ["08:00"])
    manager.update_medication(med_id, times=[])
    assert manager.get_medication(med_id).scheduled_times == []


def test_update_medication_without_times_preserves_schedule(manager):
    med_id = manager.add_medication("Aspirin", "100mg", "", ["08:00", "20:00"])
    manager.update_medication(med_id, dosage="200mg")
    assert sorted(manager.get_medication(med_id).scheduled_times) == ["08:00", "20:00"]


# ── Delete ──────────────────────────────────────────────

def test_delete_medication_returns_true_on_success(manager):
    med_id = manager.add_medication("Aspirin", "100mg", "", ["08:00"])
    assert manager.delete_medication(med_id) is True
    assert manager.get_medication(med_id) is None


def test_delete_medication_returns_false_when_missing(manager):
    assert manager.delete_medication(9999) is False


def test_delete_medication_cascades_to_times(manager):
    from database import get_connection
    med_id = manager.add_medication("Aspirin", "100mg", "", ["08:00", "20:00"])
    manager.delete_medication(med_id)
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM medication_times WHERE medication_id = ?", (med_id,)
    ).fetchall()
    conn.close()
    assert rows == []


def test_delete_medication_cascades_to_intake_log(manager):
    from database import get_connection
    med_id = manager.add_medication("Aspirin", "100mg", "", ["08:00"])
    # add_medication already populated a pending reminder for today
    manager.delete_medication(med_id)
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM intake_log WHERE medication_id = ?", (med_id,)
    ).fetchall()
    conn.close()
    assert rows == []


def test_reset_all_clears_everything(manager):
    manager.add_medication("A", "1mg", "", ["08:00"])
    manager.add_medication("B", "2mg", "", ["09:00"])
    manager.reset_all()
    assert manager.get_all_medications() == []
