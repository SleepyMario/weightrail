from __future__ import annotations

import csv
import sqlite3
from dataclasses import dataclass
from datetime import date
from pathlib import Path


DEFAULT_DB_PATH = Path.home() / ".local" / "share" / "weight-tracker-cli" / "weights.sqlite"


class DatabaseError(RuntimeError):
    """Raised when the weight database cannot be read or written."""


@dataclass(frozen=True)
class WeightEntry:
    date: str
    weight_kg: float


def connect(db_path: Path) -> sqlite3.Connection:
    try:
        db_path.parent.mkdir(parents=True, exist_ok=True)
        connection = sqlite3.connect(db_path)
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS weights (
                date TEXT PRIMARY KEY,
                weight_kg REAL NOT NULL CHECK(weight_kg > 0)
            )
            """
        )
        connection.commit()
        return connection
    except sqlite3.Error as exc:
        raise DatabaseError(f"Unable to open database {db_path}: {exc}") from exc
    except OSError as exc:
        raise DatabaseError(f"Unable to prepare database directory for {db_path}: {exc}") from exc


def upsert_weight(connection: sqlite3.Connection, date: str, weight_kg: float) -> str:
    validate_weight(weight_kg)
    try:
        existing = connection.execute(
            "SELECT 1 FROM weights WHERE date = ?",
            (date,),
        ).fetchone()
        connection.execute(
            """
            INSERT INTO weights(date, weight_kg)
            VALUES(?, ?)
            ON CONFLICT(date) DO UPDATE SET weight_kg = excluded.weight_kg
            """,
            (date, weight_kg),
        )
        connection.commit()
        return "updated" if existing else "recorded"
    except sqlite3.Error as exc:
        raise DatabaseError(f"Unable to save weight for {date}: {exc}") from exc


def list_weights(connection: sqlite3.Connection) -> list[WeightEntry]:
    try:
        rows = connection.execute(
            "SELECT date, weight_kg FROM weights ORDER BY date"
        ).fetchall()
    except sqlite3.Error as exc:
        raise DatabaseError(f"Unable to read weights: {exc}") from exc
    return [WeightEntry(date=row[0], weight_kg=float(row[1])) for row in rows]


def import_csv(connection: sqlite3.Connection, csv_path: Path) -> int:
    try:
        with csv_path.open(newline="", encoding="utf-8") as handle:
            reader = csv.DictReader(handle)
            if reader.fieldnames != ["date", "weight_kg"]:
                raise ValueError("CSV header must be: date,weight_kg")
            entries = []
            for row_number, row in enumerate(reader, start=2):
                if is_blank_row(row):
                    continue
                entries.append(
                    WeightEntry(
                        date=parse_date(row["date"], row_number),
                        weight_kg=parse_weight(row["weight_kg"]),
                    )
                )
    except OSError as exc:
        raise DatabaseError(f"Unable to read CSV {csv_path}: {exc}") from exc
    except ValueError as exc:
        raise DatabaseError(f"Invalid CSV {csv_path}: {exc}") from exc

    try:
        connection.executemany(
            """
            INSERT INTO weights(date, weight_kg)
            VALUES(?, ?)
            ON CONFLICT(date) DO UPDATE SET weight_kg = excluded.weight_kg
            """,
            [(entry.date, entry.weight_kg) for entry in entries],
        )
        connection.commit()
    except sqlite3.Error as exc:
        raise DatabaseError(f"Unable to import CSV {csv_path}: {exc}") from exc
    return len(entries)


def parse_weight(value: str) -> float:
    try:
        weight = float(value)
    except ValueError as exc:
        raise ValueError(f"weight must be a number: {value!r}") from exc
    validate_weight(weight)
    return weight


def parse_date(value: str, row_number: int | None = None) -> str:
    try:
        parsed = date.fromisoformat(value)
    except ValueError as exc:
        location = f" on row {row_number}" if row_number is not None else ""
        raise ValueError(f"date must use YYYY-MM-DD{location}: {value!r}") from exc
    return parsed.isoformat()


def validate_weight(weight_kg: float) -> None:
    if weight_kg <= 0:
        raise ValueError("weight must be positive")


def is_blank_row(row: dict[str, str | None]) -> bool:
    return all(value is None or value.strip() == "" for value in row.values())
