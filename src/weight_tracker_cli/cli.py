from __future__ import annotations

import argparse
import sys
from collections.abc import Callable
from datetime import date, datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

from . import get_version
from .db import DEFAULT_DB_PATH, DatabaseError, connect, import_csv, list_weights, parse_weight, upsert_weight
from .graph import render_graph
from .stats import calculate_trend, format_summary


TAIPEI = ZoneInfo("Asia/Taipei")


def main(argv: list[str] | None = None, today_provider: Callable[[], date] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        if args.version:
            print(f"weight-tracker {get_version()}")
            return 0

        db_path = Path(args.db_path).expanduser()
        with connect(db_path) as connection:
            if args.import_path is not None:
                imported = import_csv(connection, Path(args.import_path).expanduser())
                print(f"Imported {imported} rows.")

            if args.weight is not None:
                today = (today_provider or taipei_today)().isoformat()
                upsert_weight(connection, today, parse_weight(args.weight))

            entries = list_weights(connection)

        if args.summary:
            print(format_summary(calculate_trend(entries)))
            return 0

        if args.show or args.weight is not None or args.import_path is not None:
            print_table(entries)
            print()
            print(render_graph(entries))
            print()
            print(format_summary(calculate_trend(entries)))
            return 0

        parser.print_help()
        return 0
    except (DatabaseError, ValueError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Track daily weight in a local SQLite database.",
        epilog=(
            "A positional weight records or updates today's Asia/Taipei date. "
            f"Default database: {DEFAULT_DB_PATH}"
        ),
    )
    parser.add_argument("weight", nargs="?", help="weight in kilograms for today's Asia/Taipei date")
    parser.add_argument("--show", action="store_true", help="show recorded rows, terminal graph, and trend summary")
    parser.add_argument("--summary", action="store_true", help="show only the numeric trend summary")
    parser.add_argument("--import", dest="import_path", help="import date,weight_kg CSV rows and update existing dates")
    parser.add_argument("--db-path", default=str(DEFAULT_DB_PATH), help="SQLite database path")
    parser.add_argument("--version", action="store_true", help="show version and exit")
    return parser


def taipei_today() -> date:
    return taipei_date_from_datetime(datetime.now(timezone.utc))


def taipei_date_from_datetime(value: datetime) -> date:
    return value.astimezone(TAIPEI).date()


def print_table(entries) -> None:
    if not entries:
        print("No measurements recorded.")
        return

    print("Date        Weight kg")
    print("----------  ---------")
    for entry in entries:
        print(f"{entry.date}  {entry.weight_kg:9.1f}")
