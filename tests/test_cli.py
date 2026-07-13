from datetime import date, datetime, timezone

import pytest

from weightrail import cli
from weightrail.db import DEFAULT_DB_PATH


def test_show_empty_database_is_clear(tmp_path, capsys):
    exit_code = cli.main(["--db-path", str(tmp_path / "weights.sqlite"), "--show"])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "No measurements recorded." in captured.out
    assert captured.err == ""


def test_positional_weight_uses_injected_taipei_date_and_updates_existing_row(tmp_path, capsys):
    db_path = tmp_path / "weights.sqlite"
    today = lambda: date(2026, 7, 6)

    assert cli.main(["--db-path", str(db_path), "122.8"], today_provider=today) == 0
    capsys.readouterr()
    assert cli.main(["--db-path", str(db_path), "123.4"], today_provider=today) == 0

    captured = capsys.readouterr()
    assert "Updated 123.4 kg for 2026-07-06." in captured.out
    assert "2026-07-06      123.4" in captured.out
    assert "2026-07-06      122.8" not in captured.out


def test_stats_command_with_no_data_is_clear(tmp_path, capsys):
    exit_code = cli.main(["--db-path", str(tmp_path / "weights.sqlite"), "stats"])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert captured.out == "No measurements recorded.\n"
    assert captured.err == ""


def test_stats_flag_rejects_weight_argument(tmp_path, capsys):
    exit_code = cli.main(["--db-path", str(tmp_path / "weights.sqlite"), "--stats", "122.0"])

    captured = capsys.readouterr()
    assert exit_code == 1
    assert captured.out == ""
    assert "--stats cannot be combined with a weight" in captured.err


def test_stats_command_reports_multiple_entry_stats(tmp_path, capsys):
    csv_path = tmp_path / "seed.csv"
    csv_path.write_text(
        "date,weight_kg\n"
        "2026-07-01,122.0\n"
        "2026-07-03,121.0\n"
        "2026-07-07,120.0\n",
        encoding="utf-8",
    )
    db_path = tmp_path / "weights.sqlite"

    assert cli.main(["--db-path", str(db_path), "--import", str(csv_path)]) == 0
    capsys.readouterr()
    assert cli.main(["--db-path", str(db_path), "stats"]) == 0

    captured = capsys.readouterr()
    assert "Stats" in captured.out
    assert "Entries: 3" in captured.out
    assert "Latest weight: 120.0 kg" in captured.out
    assert "Change since previous: -1.0 kg" in captured.out
    assert "Total change: -2.0 kg" in captured.out
    assert "7-day average: 121.0 kg" in captured.out
    assert "Highest: 122.0 kg on 2026-07-01" in captured.out
    assert "Lowest: 120.0 kg on 2026-07-07" in captured.out
    assert "Missing days: 4" in captured.out


def test_import_show_and_summary_use_custom_db_path(tmp_path, capsys):
    csv_path = tmp_path / "seed.csv"
    csv_path.write_text("date,weight_kg\n2026-07-01,122.0\n2026-07-03,123.0\n", encoding="utf-8")
    db_path = tmp_path / "weights.sqlite"

    assert cli.main(["--db-path", str(db_path), "--import", str(csv_path)]) == 0
    assert cli.main(["--db-path", str(db_path), "--summary"]) == 0

    captured = capsys.readouterr()
    assert "Imported 2 rows." in captured.out
    assert "2026-07-01      122.0" in captured.out
    assert "Measurements: 2" in captured.out


def test_invalid_weight_returns_nonzero_and_uses_stderr(tmp_path, capsys):
    exit_code = cli.main(["--db-path", str(tmp_path / "weights.sqlite"), "0"])

    captured = capsys.readouterr()
    assert exit_code == 1
    assert captured.out == ""
    assert "weight must be positive" in captured.err


def test_invalid_command_returns_nonzero(capsys):
    with pytest.raises(SystemExit) as exc:
        cli.main(["--does-not-exist"])

    captured = capsys.readouterr()
    assert exc.value.code == 2
    assert "unrecognized arguments" in captured.err


def test_help_mentions_default_database_and_taipei(capsys):
    with pytest.raises(SystemExit) as exc:
        cli.main(["--help"])

    captured = capsys.readouterr()
    assert exc.value.code == 0
    assert "Default database:" in captured.out
    assert DEFAULT_DB_PATH.name in captured.out
    assert "Asia/Taipei" in captured.out


def test_version_output(capsys):
    exit_code = cli.main(["--version"])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert captured.out == "weightrail 0.2.0\n"
    assert captured.err == ""


def test_taipei_timezone_constant_is_used():
    assert cli.TAIPEI.key == "Asia/Taipei"


def test_taipei_date_boundary_uses_taipei_not_machine_timezone():
    before_midnight = datetime(2026, 7, 5, 15, 59, tzinfo=timezone.utc)
    after_midnight = datetime(2026, 7, 5, 16, 1, tzinfo=timezone.utc)

    assert cli.taipei_date_from_datetime(before_midnight) == date(2026, 7, 5)
    assert cli.taipei_date_from_datetime(after_midnight) == date(2026, 7, 6)
