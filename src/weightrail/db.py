from __future__ import annotations

import csv
import os
import shutil
import sqlite3
import tempfile
from dataclasses import dataclass
from datetime import date
from pathlib import Path


def _data_home() -> Path:
    configured = os.environ.get("XDG_DATA_HOME")
    if configured:
        return Path(configured).expanduser()
    if os.name == "nt" and os.environ.get("LOCALAPPDATA"):
        return Path(os.environ["LOCALAPPDATA"])
    return Path.home() / ".local" / "share"


DEFAULT_DB_PATH = _data_home() / "weightrail" / "weights.sqlite"
LEGACY_DB_PATH = Path.home() / ".local" / "share" / "weight-tracker-cli" / "weights.sqlite"


class DatabaseError(RuntimeError):
    """Raised when the weight database cannot be read or written."""


@dataclass(frozen=True)
class WeightEntry:
    date: str
    weight_kg: float


@dataclass(frozen=True)
class VitalEntry:
    date: str
    systolic_mmhg: int
    diastolic_mmhg: int
    resting_heart_rate_bpm: int


def migrate_legacy_database(
    new_path: Path = DEFAULT_DB_PATH,
    legacy_path: Path = LEGACY_DB_PATH,
) -> bool:
    """Atomically copy a legacy default database without replacing new data."""
    if new_path.exists() or not legacy_path.is_file():
        return False

    temporary_path: Path | None = None
    try:
        new_path.parent.mkdir(parents=True, exist_ok=True)
        file_descriptor, temporary_name = tempfile.mkstemp(
            prefix=f".{new_path.name}.",
            suffix=".migrating",
            dir=new_path.parent,
        )
        os.close(file_descriptor)
        temporary_path = Path(temporary_name)
        shutil.copy2(legacy_path, temporary_path)
        # Windows rejects fsync() on a read-only descriptor with EBADF.
        # Opening the copied file read/write keeps the durability step portable.
        with temporary_path.open("r+b") as handle:
            os.fsync(handle.fileno())
        try:
            os.link(temporary_path, new_path)
        except FileExistsError:
            return False
        return True
    except OSError as exc:
        raise DatabaseError(
            f"Unable to migrate the legacy database from {legacy_path} to {new_path}: {exc}"
        ) from exc
    finally:
        if temporary_path is not None:
            try:
                temporary_path.unlink(missing_ok=True)
            except OSError:
                pass


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
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS vitals (
                date TEXT PRIMARY KEY,
                systolic_mmhg INTEGER NOT NULL CHECK(systolic_mmhg > 0),
                diastolic_mmhg INTEGER NOT NULL CHECK(diastolic_mmhg > 0),
                resting_heart_rate_bpm INTEGER NOT NULL
                    CHECK(resting_heart_rate_bpm > 0),
                CHECK(systolic_mmhg > diastolic_mmhg)
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


def upsert_vitals(
    connection: sqlite3.Connection,
    date: str,
    systolic_mmhg: int,
    diastolic_mmhg: int,
    resting_heart_rate_bpm: int,
) -> str:
    validate_vitals(systolic_mmhg, diastolic_mmhg, resting_heart_rate_bpm)
    try:
        existing = connection.execute(
            "SELECT 1 FROM vitals WHERE date = ?",
            (date,),
        ).fetchone()
        connection.execute(
            """
            INSERT INTO vitals(
                date,
                systolic_mmhg,
                diastolic_mmhg,
                resting_heart_rate_bpm
            )
            VALUES(?, ?, ?, ?)
            ON CONFLICT(date) DO UPDATE SET
                systolic_mmhg = excluded.systolic_mmhg,
                diastolic_mmhg = excluded.diastolic_mmhg,
                resting_heart_rate_bpm = excluded.resting_heart_rate_bpm
            """,
            (date, systolic_mmhg, diastolic_mmhg, resting_heart_rate_bpm),
        )
        connection.commit()
        return "updated" if existing else "recorded"
    except sqlite3.Error as exc:
        raise DatabaseError(f"Unable to save vitals for {date}: {exc}") from exc


def list_vitals(connection: sqlite3.Connection) -> list[VitalEntry]:
    try:
        rows = connection.execute(
            """
            SELECT date, systolic_mmhg, diastolic_mmhg,
                   resting_heart_rate_bpm
            FROM vitals
            ORDER BY date
            """
        ).fetchall()
    except sqlite3.Error as exc:
        raise DatabaseError(f"Unable to read vitals: {exc}") from exc
    return [
        VitalEntry(
            date=row[0],
            systolic_mmhg=int(row[1]),
            diastolic_mmhg=int(row[2]),
            resting_heart_rate_bpm=int(row[3]),
        )
        for row in rows
    ]


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


def parse_vital(value: str, name: str) -> int:
    try:
        parsed = int(value)
    except ValueError as exc:
        raise ValueError(f"{name} must be a whole number: {value!r}") from exc
    if parsed <= 0:
        raise ValueError(f"{name} must be positive")
    return parsed


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


def validate_vitals(
    systolic_mmhg: int,
    diastolic_mmhg: int,
    resting_heart_rate_bpm: int,
) -> None:
    for value, name in (
        (systolic_mmhg, "upper blood pressure"),
        (diastolic_mmhg, "lower blood pressure"),
        (resting_heart_rate_bpm, "resting heart rate"),
    ):
        if not isinstance(value, int) or isinstance(value, bool):
            raise ValueError(f"{name} must be a whole number")
        if value <= 0:
            raise ValueError(f"{name} must be positive")
    if systolic_mmhg <= diastolic_mmhg:
        raise ValueError("upper blood pressure must be higher than lower blood pressure")


def is_blank_row(row: dict[str, str | None]) -> bool:
    return all(value is None or value.strip() == "" for value in row.values())
