from contextlib import nullcontext
from datetime import date

import pytest

from weightrail import gui
from weightrail.db import WeightEntry, connect, list_weights
from weightrail.gui_chart import (
    ALL_SERIES,
    LINEAR_TREND,
    MEASUREMENTS,
    MONTHLY_TREND,
    WEEKLY_TREND,
    chart_series_availability,
    prepare_chart_data,
)


def test_gui_module_imports_without_loading_gtk():
    assert gui.RECENT_ENTRY_LIMIT == 10


def test_packaged_stylesheet_is_registered():
    calls = []

    class Provider:
        def load_from_data(self, css):
            calls.append(("css", css))

    class FakeStyleContext:
        @staticmethod
        def add_provider_for_screen(screen, provider, priority):
            calls.append(("provider", screen, provider, priority))

    class Gtk:
        STYLE_PROVIDER_PRIORITY_APPLICATION = 600
        CssProvider = Provider
        StyleContext = FakeStyleContext

    screen = object()
    provider = gui.install_stylesheet(Gtk, screen)

    css = next(value for name, value in calls if name == "css")
    assert b".card" in css
    assert b"button.primary-action" in css
    assert ("provider", screen, provider, 600) in calls


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


def test_keyboard_interrupt_quits_gtk_cleanly(monkeypatch, tmp_path):
    calls = []

    class Gtk:
        @staticmethod
        def main():
            raise KeyboardInterrupt

        @staticmethod
        def main_quit():
            calls.append("quit")

    class Window:
        def connect(self, *_args):
            pass

        def show_all(self):
            pass

    monkeypatch.setattr(gui, "load_gtk", lambda: Gtk)
    monkeypatch.setattr(gui, "load_chart_backend", lambda: (object(), object()))
    monkeypatch.setattr(gui, "WeightrailWindow", lambda *_args: Window())

    assert gui.main(["--db-path", str(tmp_path / "weights.sqlite")]) == 130
    assert calls == ["quit"]


def test_normal_gtk_shutdown_remains_successful(monkeypatch, tmp_path):
    calls = []

    class Gtk:
        @staticmethod
        def main():
            calls.append("main")

        @staticmethod
        def main_quit():
            calls.append("quit")

    class Window:
        def connect(self, *_args):
            pass

        def show_all(self):
            pass

    monkeypatch.setattr(gui, "load_gtk", lambda: Gtk)
    monkeypatch.setattr(gui, "load_chart_backend", lambda: (object(), object()))
    monkeypatch.setattr(gui, "WeightrailWindow", lambda *_args: Window())

    assert gui.main(["--db-path", str(tmp_path / "weights.sqlite")]) == 0
    assert calls == ["main"]


def test_unrelated_gtk_exception_is_not_masked(monkeypatch, tmp_path):
    class Gtk:
        @staticmethod
        def main():
            raise RuntimeError("main-loop failure")

        @staticmethod
        def main_quit():
            raise AssertionError("must not handle unrelated exceptions")

    class Window:
        def connect(self, *_args):
            pass

        def show_all(self):
            pass

    monkeypatch.setattr(gui, "load_gtk", lambda: Gtk)
    monkeypatch.setattr(gui, "load_chart_backend", lambda: (object(), object()))
    monkeypatch.setattr(gui, "WeightrailWindow", lambda *_args: Window())

    with pytest.raises(RuntimeError, match="main-loop failure"):
        gui.main(["--db-path", str(tmp_path / "weights.sqlite")])


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

    class Window:
        db_path = tmp_path / "weights.sqlite"
        status_label = StatusLabel()

        def refresh_stats(self, stats):
            refreshed.append(("stats", stats))

        def refresh_chart(self, values):
            refreshed.append(("chart", values))

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


def test_record_flow_still_updates_today_and_refreshes(monkeypatch, tmp_path):
    db_path = tmp_path / "weights.sqlite"
    refreshed = []

    class Entry:
        def __init__(self):
            self.text = "121.5"

        def get_text(self):
            return self.text

        def set_text(self, value):
            self.text = value

    class StatusLabel:
        def set_text(self, value):
            self.text = value

    window = type("Window", (), {})()
    window.db_path = db_path
    window.weight_entry = Entry()
    window.status_label = StatusLabel()
    window.refresh = lambda: refreshed.append(True)
    monkeypatch.setattr(gui, "taipei_today", lambda: date(2026, 8, 19))

    gui.WeightrailWindow.on_record_clicked(window)

    with connect(db_path) as connection:
        entries = list_weights(connection)
    assert entries == [WeightEntry("2026-08-19", 121.5)]
    assert window.weight_entry.text == ""
    assert window.status_label.text == "Recorded 121.5 kg for 2026-08-19."
    assert refreshed == [True]


def test_recent_entries_remain_latest_first_and_limited():
    calls = []

    class Store:
        def clear(self):
            calls.append(("clear",))

        def append(self, row):
            calls.append(("append", row))

    window = type("Window", (), {})()
    window.recent_store = Store()
    entries = [
        WeightEntry(f"2026-08-{day:02d}", 100.0 + day)
        for day in range(1, 13)
    ]

    gui.WeightrailWindow.refresh_recent(window, entries)

    rows = [call[1] for call in calls if call[0] == "append"]
    assert len(rows) == gui.RECENT_ENTRY_LIMIT
    assert rows[0] == ["2026-08-12", "112.0"]
    assert rows[-1] == ["2026-08-03", "103.0"]


def test_line_visibility_defaults_and_unavailable_controls():
    state = gui.LineVisibilityState()
    state.update_availability(
        {
            MEASUREMENTS: True,
            LINEAR_TREND: False,
            WEEKLY_TREND: False,
            MONTHLY_TREND: False,
        }
    )

    assert state.selected == {
        MEASUREMENTS: True,
        LINEAR_TREND: False,
        WEEKLY_TREND: False,
        MONTHLY_TREND: False,
    }
    assert state.visible_series == {MEASUREMENTS}

    class Control:
        def set_sensitive(self, value):
            self.sensitive = value

        def set_active(self, value):
            self.active = value

    window = type("Window", (), {})()
    window._syncing_line_controls = False
    window.line_visibility = state
    window.line_controls = {series: Control() for series in ALL_SERIES}
    gui.WeightrailWindow.sync_line_controls(window)

    assert window.line_controls[MEASUREMENTS].sensitive
    assert window.line_controls[MEASUREMENTS].active
    for series in (LINEAR_TREND, WEEKLY_TREND, MONTHLY_TREND):
        assert not window.line_controls[series].sensitive
        assert not window.line_controls[series].active


def test_weekly_and_monthly_lines_default_on_when_they_become_available():
    state = gui.LineVisibilityState()
    initial_data = prepare_chart_data(
        [WeightEntry("2026-01-05", 100.0)],
        current_date=date(2026, 1, 18),
    )
    state.update_availability(chart_series_availability(initial_data))
    assert not state.available[WEEKLY_TREND]
    assert not state.selected[WEEKLY_TREND]
    assert not state.available[MONTHLY_TREND]
    assert not state.selected[MONTHLY_TREND]

    weekly_data = prepare_chart_data(
        [
            WeightEntry("2026-01-05", 100.0),
            WeightEntry("2026-01-12", 99.0),
        ],
        current_date=date(2026, 1, 18),
    )
    state.update_availability(chart_series_availability(weekly_data))
    assert state.available[WEEKLY_TREND]
    assert state.selected[WEEKLY_TREND]

    monthly_data = prepare_chart_data(
        [
            WeightEntry("2026-01-05", 100.0),
            WeightEntry("2026-02-05", 99.0),
        ],
        current_date=date(2026, 2, 28),
    )
    state.update_availability(chart_series_availability(monthly_data))
    assert state.available[MONTHLY_TREND]
    assert state.selected[MONTHLY_TREND]


def test_manually_hidden_line_survives_refresh_and_toggle_redraws():
    state = gui.LineVisibilityState()
    availability = {series: True for series in ALL_SERIES}
    state.update_availability(availability)
    assert state.visible_series == frozenset(ALL_SERIES)

    rendered = []

    class Chart:
        def render(self, chart_data, visible_series):
            rendered.append((chart_data, visible_series))

    class Button:
        def __init__(self, active):
            self.active = active

        def get_active(self):
            return self.active

    window = type("Window", (), {})()
    window._syncing_line_controls = False
    window.line_visibility = state
    window.weight_chart = Chart()
    window.chart_data = object()

    gui.WeightrailWindow.on_line_toggled(
        window, Button(False), WEEKLY_TREND
    )
    assert not state.selected[WEEKLY_TREND]
    assert WEEKLY_TREND not in rendered[-1][1]

    state.update_availability(availability)
    assert not state.selected[WEEKLY_TREND]

    gui.WeightrailWindow.on_line_toggled(
        window, Button(True), WEEKLY_TREND
    )
    assert state.selected[WEEKLY_TREND]
    assert rendered[-1] == (window.chart_data, frozenset(ALL_SERIES))
