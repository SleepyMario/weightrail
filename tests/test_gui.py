from contextlib import nullcontext

import pytest

from weightrail import gui
from weightrail.db import WeightEntry


def test_gui_module_imports_without_loading_gtk():
    assert gui.RECENT_ENTRY_LIMIT == 10


def test_gui_help_does_not_require_display(capsys):
    with pytest.raises(SystemExit) as exc:
        gui.main(["--help"])

    captured = capsys.readouterr()
    assert exc.value.code == 0
    assert "Small GTK frontend" in captured.out
    assert "--db-path" in captured.out


def test_gui_reports_missing_matplotlib_clearly(monkeypatch, capsys):
    monkeypatch.setattr(gui, "load_gtk", lambda: object())

    def unavailable_backend():
        raise ImportError("No module named 'matplotlib'")

    monkeypatch.setattr(gui, "load_chart_backend", unavailable_backend)

    assert gui.main([]) == 1
    captured = capsys.readouterr()
    assert "requires Matplotlib with GTK 3 support" in captured.err
    assert "weightrail[gui]" in captured.err


def test_refresh_reuses_one_loaded_entry_list(monkeypatch, tmp_path):
    entries = [WeightEntry("2026-07-01", 100.0)]
    list_calls = []
    refreshed = []

    monkeypatch.setattr(gui, "connect", lambda _path: nullcontext(object()))

    def fake_list_weights(_connection):
        list_calls.append(True)
        return entries

    monkeypatch.setattr(gui, "list_weights", fake_list_weights)
    monkeypatch.setattr(gui, "calculate_stats", lambda values: ("stats", values))

    class StatusLabel:
        def get_text(self):
            return ""

        def set_text(self, value):
            refreshed.append(("status", value))

    class Chart:
        def refresh(self, values):
            refreshed.append(("chart", values))

    class Window:
        db_path = tmp_path / "weights.sqlite"
        status_label = StatusLabel()
        weight_chart = Chart()

        def refresh_stats(self, stats):
            refreshed.append(("stats", stats))

        def refresh_recent(self, values):
            refreshed.append(("recent", values))

    gui.WeightrailWindow.refresh(Window())

    assert len(list_calls) == 1
    chart_entries = next(value for name, value in refreshed if name == "chart")
    recent_entries = next(value for name, value in refreshed if name == "recent")
    stats = next(value for name, value in refreshed if name == "stats")
    assert chart_entries is entries
    assert recent_entries is entries
    assert stats[1] is entries
