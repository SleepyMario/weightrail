import pytest

from weight_tracker_cli.db import WeightEntry
from weight_tracker_cli.graph import render_graph
from weight_tracker_cli.stats import calculate_stats, calculate_trend, format_stats, format_summary


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

        def scatter(self, days, weights, marker):
            calls.append(("scatter", days, weights, marker))

        def plot(self, days, weights):
            calls.append(("plot", days, weights))

        def build(self):
            return "graph"

    monkeypatch.setattr("weight_tracker_cli.graph.plt", FakePlot())

    assert render_graph([WeightEntry("2026-07-01", 122.0), WeightEntry("2026-07-03", 123.0)]) == "graph"
    assert ("scatter", [0, 2], [122.0, 123.0], "dot") in calls
    assert ("plot", [0, 2], [122.0, 123.0]) in calls
