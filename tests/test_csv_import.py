import pytest

from weightrail import db


def write_csv(path, text):
    path.write_text(text, encoding="utf-8")
    return path


def test_valid_csv_imports_and_updates_duplicate_dates(tmp_path):
    csv_path = write_csv(
        tmp_path / "seed.csv",
        "date,weight_kg\n2026-07-01,122.0\n2026-07-01,123.0\n2026-07-03,124.0\n",
    )
    db_path = tmp_path / "weights.sqlite"

    with db.connect(db_path) as connection:
        count = db.import_csv(connection, csv_path)
        entries = db.list_weights(connection)

    assert count == 3
    assert [(entry.date, entry.weight_kg) for entry in entries] == [
        ("2026-07-01", 123.0),
        ("2026-07-03", 124.0),
    ]


def test_malformed_date_fails_before_writing_rows(tmp_path):
    csv_path = write_csv(tmp_path / "bad.csv", "date,weight_kg\n2026-07-01,122.0\nbad,123.0\n")
    db_path = tmp_path / "weights.sqlite"

    with db.connect(db_path) as connection:
        with pytest.raises(db.DatabaseError, match="YYYY-MM-DD"):
            db.import_csv(connection, csv_path)
        assert db.list_weights(connection) == []


def test_malformed_weight_fails_before_writing_rows(tmp_path):
    csv_path = write_csv(tmp_path / "bad.csv", "date,weight_kg\n2026-07-01,122.0\n2026-07-02,bad\n")
    db_path = tmp_path / "weights.sqlite"

    with db.connect(db_path) as connection:
        with pytest.raises(db.DatabaseError, match="weight must be a number"):
            db.import_csv(connection, csv_path)
        assert db.list_weights(connection) == []


def test_missing_required_columns_fail_clearly(tmp_path):
    csv_path = write_csv(tmp_path / "bad.csv", "date,weight\n2026-07-01,122.0\n")

    with db.connect(tmp_path / "weights.sqlite") as connection:
        with pytest.raises(db.DatabaseError, match="CSV header must be: date,weight_kg"):
            db.import_csv(connection, csv_path)


def test_blank_rows_are_ignored(tmp_path):
    csv_path = write_csv(tmp_path / "seed.csv", "date,weight_kg\n2026-07-01,122.0\n,\n\n2026-07-02,123.0\n")

    with db.connect(tmp_path / "weights.sqlite") as connection:
        count = db.import_csv(connection, csv_path)
        entries = db.list_weights(connection)

    assert count == 2
    assert [entry.date for entry in entries] == ["2026-07-01", "2026-07-02"]


def test_missing_csv_file_fails_clearly(tmp_path):
    with db.connect(tmp_path / "weights.sqlite") as connection:
        with pytest.raises(db.DatabaseError, match="Unable to read CSV"):
            db.import_csv(connection, tmp_path / "missing.csv")
