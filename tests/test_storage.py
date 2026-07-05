from pathlib import Path

import pytest

from weight_tracker_cli import db
from weight_tracker_cli.db import DatabaseError, WeightEntry


def test_creates_new_database_and_schema(tmp_path):
    db_path = tmp_path / "weights.sqlite"

    with db.connect(db_path) as connection:
        columns = connection.execute("PRAGMA table_info(weights)").fetchall()

    assert db_path.exists()
    assert [column[1] for column in columns] == ["date", "weight_kg"]


def test_adds_updates_and_reads_records_in_date_order(tmp_path):
    db_path = tmp_path / "weights.sqlite"

    with db.connect(db_path) as connection:
        db.upsert_weight(connection, "2026-07-02", 122.8)
        db.upsert_weight(connection, "2026-07-01", 122.0)
        db.upsert_weight(connection, "2026-07-02", 123.0)
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
