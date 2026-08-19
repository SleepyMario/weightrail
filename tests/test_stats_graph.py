import sys
from datetime import date

import pytest

from weightrail.db import WeightEntry
from weightrail.graph import render_graph
from weightrail.stats import calculate_stats, calculate_trend, format_stats, format_summary


def test_summary_zero_records_is_clear():
    assert calculate_trend([]) is None
    assert format_summary(None) == "No measurements recorded."
    assert calculate_stats([]) is None
    assert format_stats(None) == "No measurements recorded."


def test_summary_one_record_has_zero_slope():
    summary = calculate_trend([WeightEntry("2026-07-01", 122.0)])
    stats = calculate_stats([WeightEntry("2026-07-01", 122.0)])

    assert summary is not None
    assert summary.slope_kg_per_day == 0.0
    assert summary.slope_kg_per_week == 0.0
    assert "Measurements: 1" in format_summary(summary)
    assert stats is not None
    assert stats.entries == 1
    assert stats.latest_weight == 122.0
    assert stats.change_since_previous is None
    assert stats.total_change == 0.0
    assert stats.average_7_day is None
    assert stats.average_30_day is None
    assert stats.highest_weight == 122.0
    assert stats.lowest_weight == 122.0
    assert stats.missing_days == 0
    formatted = format_stats(stats)
    assert "Entries: 1" in formatted
    assert "Change since previous: n/a" in formatted
    assert "7-day average: n/a" in formatted


def test_regression_uses_recorded_dates_and_handles_missing_days():
    entries = [
        WeightEntry("2026-07-01", 100.0),
        WeightEntry("2026-07-03", 104.0),
        WeightEntry("2026-07-06", 110.0),
    ]
    summary = calculate_trend(entries)
    stats = calculate_stats(entries)

    assert summary is not None
    assert summary.first_date == "2026-07-01"
    assert summary.latest_date == "2026-07-06"
    assert summary.slope_kg_per_day == pytest.approx(2.0)
    assert summary.slope_kg_per_week == pytest.approx(14.0)
    assert summary.intercept == pytest.approx(100.0)
    assert stats is not None
    assert stats.entries == 3
    assert stats.latest_weight == 110.0
    assert stats.previous_weight == 104.0
    assert stats.change_since_previous == pytest.approx(6.0)
    assert stats.total_change == pytest.approx(10.0)
    assert stats.average_7_day == pytest.approx((100.0 + 104.0 + 110.0) / 3)
    assert stats.average_30_day == pytest.approx((100.0 + 104.0 + 110.0) / 3)
    assert stats.highest_date == "2026-07-06"
    assert stats.highest_weight == 110.0
    assert stats.lowest_date == "2026-07-01"
    assert stats.lowest_weight == 100.0
    assert stats.missing_days == 3


def test_empty_graph_is_clear():
    assert render_graph([]) == "No measurements to graph."


def test_graph_uses_plotext_without_crashing(monkeypatch):
    calls = []

    class FakePlot:
        def clear_figure(self):
            calls.append(("clear_figure",))

        def plotsize(self, width, height):
            calls.append(("plotsize", width, height))

        def title(self, value):
            calls.append(("title", value))

        def xlabel(self, value):
            calls.append(("xlabel", value))

        def ylabel(self, value):
            calls.append(("ylabel", value))

        def scatter(self, days, weights, **kwargs):
            calls.append(("scatter", days, weights, kwargs))

        def plot(self, days, weights, **kwargs):
            calls.append(("plot", days, weights, kwargs))

        def build(self):
            return "graph"

    monkeypatch.setitem(sys.modules, "plotext", FakePlot())

    assert render_graph([WeightEntry("2026-07-01", 122.0), WeightEntry("2026-07-03", 123.0)]) == "graph"
    assert (
        "scatter",
        [0, 2],
        [122.0, 123.0],
        {"marker": "dot", "label": "Measurements"},
    ) in calls
    assert ("plot", [0, 2], [122.0, 123.0], {}) in calls
    assert (
        "plot",
        [0, 2],
        pytest.approx([122.0, 123.0]),
        {"color": "orange", "label": "Linear trend"},
    ) in calls


def test_terminal_graph_uses_shared_period_trends_with_actual_dates(monkeypatch):
    calls = []

    class FakePlot:
        def clear_figure(self):
            pass

        def plotsize(self, _width, _height):
            pass

        def title(self, _value):
            pass

        def xlabel(self, _value):
            pass

        def ylabel(self, _value):
            pass

        def scatter(self, days, weights, **kwargs):
            calls.append(("scatter", days, weights, kwargs))

        def plot(self, days, weights, **kwargs):
            calls.append(("plot", days, weights, kwargs))

        def build(self):
            return "graph"

    monkeypatch.setitem(sys.modules, "plotext", FakePlot())
    entries = [
        WeightEntry("2026-01-10", 100.0),
        WeightEntry("2026-02-10", 95.0),
        WeightEntry("2026-03-10", 90.0),
    ]

    assert render_graph(entries, current_date=date(2026, 4, 30)) == "graph"
    monthly_call = next(
        call for call in calls if call[3].get("label") == "Monthly trend"
    )
    weekly_call = next(
        call for call in calls if call[3].get("label") == "Weekly trend"
    )
    assert monthly_call[1][0] == (date(2026, 1, 31) - date(2026, 1, 10)).days
    assert monthly_call[1][-1] == (date(2026, 3, 31) - date(2026, 1, 10)).days
    assert monthly_call[3] == {
        "marker": "braille",
        "color": "magenta",
        "label": "Monthly trend",
    }
    assert weekly_call[1][0] == (date(2026, 1, 11) - date(2026, 1, 10)).days
    assert weekly_call[1][-1] == (date(2026, 3, 15) - date(2026, 1, 10)).days
    assert weekly_call[3] == {
        "marker": "hd",
        "color": "cyan",
        "label": "Weekly trend",
    }


def test_graph_reports_when_optional_plotext_is_unavailable(monkeypatch):
    monkeypatch.setitem(sys.modules, "plotext", None)

    assert render_graph([WeightEntry("2026-07-01", 122.0)]) == (
        "Terminal graph unavailable: install the optional 'plotext' dependency."
    )
