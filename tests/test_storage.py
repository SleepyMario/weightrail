import stat
from pathlib import Path

import pytest

from weightrail import db
from weightrail.db import DatabaseError, WeightEntry


def test_creates_new_database_and_schema(tmp_path):
    db_path = tmp_path / "weights.sqlite"

    with db.connect(db_path) as connection:
        columns = connection.execute("PRAGMA table_info(weights)").fetchall()

    assert db_path.exists()
    assert [column[1] for column in columns] == ["date", "weight_kg"]


def test_adds_updates_and_reads_records_in_date_order(tmp_path):
    db_path = tmp_path / "weights.sqlite"

    with db.connect(db_path) as connection:
        assert db.upsert_weight(connection, "2026-07-02", 122.8) == "recorded"
        assert db.upsert_weight(connection, "2026-07-01", 122.0) == "recorded"
        assert db.upsert_weight(connection, "2026-07-02", 123.0) == "updated"
        entries = db.list_weights(connection)

    assert entries == [
        WeightEntry(date="2026-07-01", weight_kg=122.0),
        WeightEntry(date="2026-07-02", weight_kg=123.0),
    ]


def test_missing_dates_are_absent_rows(tmp_path):
    db_path = tmp_path / "weights.sqlite"

    with db.connect(db_path) as connection:
        db.upsert_weight(connection, "2026-07-01", 122.0)
        db.upsert_weight(connection, "2026-07-03", 123.0)
        entries = db.list_weights(connection)

    assert [entry.date for entry in entries] == ["2026-07-01", "2026-07-03"]


def test_alternate_db_path_creates_parent_directories(tmp_path):
    db_path = tmp_path / "nested" / "weights.sqlite"

    with db.connect(db_path) as connection:
        db.upsert_weight(connection, "2026-07-01", 122.0)

    assert db_path.exists()


def test_migration_with_no_legacy_database_does_nothing(tmp_path):
    new_path = tmp_path / "new" / "weights.sqlite"
    legacy_path = tmp_path / "legacy" / "weights.sqlite"

    assert db.migrate_legacy_database(new_path, legacy_path) is False
    assert not new_path.exists()


def test_migration_copies_legacy_database_and_preserves_mode(tmp_path):
    legacy_path = tmp_path / "legacy" / "weights.sqlite"
    new_path = tmp_path / "new" / "weights.sqlite"
    legacy_path.parent.mkdir()
    legacy_path.write_bytes(b"legacy database contents")
    legacy_path.chmod(0o640)

    assert db.migrate_legacy_database(new_path, legacy_path) is True
    assert new_path.read_bytes() == legacy_path.read_bytes()
    assert stat.S_IMODE(new_path.stat().st_mode) == 0o640
    assert legacy_path.read_bytes() == b"legacy database contents"


def test_migration_with_new_database_only_uses_new_database(tmp_path):
    new_path = tmp_path / "new" / "weights.sqlite"
    legacy_path = tmp_path / "legacy" / "weights.sqlite"
    new_path.parent.mkdir()
    new_path.write_bytes(b"new database")

    assert db.migrate_legacy_database(new_path, legacy_path) is False
    assert new_path.read_bytes() == b"new database"


def test_migration_never_overwrites_new_database_when_both_exist(tmp_path):
    new_path = tmp_path / "new" / "weights.sqlite"
    legacy_path = tmp_path / "legacy" / "weights.sqlite"
    new_path.parent.mkdir()
    legacy_path.parent.mkdir()
    new_path.write_bytes(b"new database")
    legacy_path.write_bytes(b"legacy database")

    assert db.migrate_legacy_database(new_path, legacy_path) is False
    assert new_path.read_bytes() == b"new database"
    assert legacy_path.read_bytes() == b"legacy database"


def test_migration_copy_failure_leaves_both_paths_safe(tmp_path, monkeypatch):
    new_path = tmp_path / "new" / "weights.sqlite"
    legacy_path = tmp_path / "legacy" / "weights.sqlite"
    legacy_path.parent.mkdir()
    legacy_path.write_bytes(b"legacy database")

    def fail_copy(*_args, **_kwargs):
        raise OSError("simulated copy failure")

    monkeypatch.setattr(db.shutil, "copy2", fail_copy)
    with pytest.raises(DatabaseError, match="simulated copy failure"):
        db.migrate_legacy_database(new_path, legacy_path)

    assert not new_path.exists()
    assert legacy_path.read_bytes() == b"legacy database"
    assert list(new_path.parent.glob("*.migrating")) == []


def test_repeated_startup_after_migration_does_not_copy_again(tmp_path):
    new_path = tmp_path / "new" / "weights.sqlite"
    legacy_path = tmp_path / "legacy" / "weights.sqlite"
    legacy_path.parent.mkdir()
    legacy_path.write_bytes(b"legacy database")

    assert db.migrate_legacy_database(new_path, legacy_path) is True
    new_path.write_bytes(b"current database")
    assert db.migrate_legacy_database(new_path, legacy_path) is False
    assert new_path.read_bytes() == b"current database"
    assert legacy_path.read_bytes() == b"legacy database"


def test_corrupt_database_fails_cleanly(tmp_path):
    db_path = tmp_path / "weights.sqlite"
    db_path.write_text("not sqlite", encoding="utf-8")

    with pytest.raises(DatabaseError, match="file is not a database"):
        db.connect(db_path)


@pytest.mark.parametrize("value,expected", [("122.8", 122.8), ("1", 1.0), ("9999", 9999.0)])
def test_valid_decimal_weights_are_accepted(value, expected):
    assert db.parse_weight(value) == expected


@pytest.mark.parametrize("value", ["not-a-number", "0", "-1"])
def test_invalid_weights_are_rejected(value):
    with pytest.raises(ValueError):
        db.parse_weight(value)


def test_invalid_date_is_rejected():
    with pytest.raises(ValueError, match="YYYY-MM-DD"):
        db.parse_date("07/05/2026")
