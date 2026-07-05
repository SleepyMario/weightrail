import pytest

from weight_tracker_cli.db import WeightEntry
from weight_tracker_cli.graph import render_graph
from weight_tracker_cli.stats import calculate_trend, format_summary


def test_summary_zero_records_is_clear():
    assert calculate_trend([]) is None
    assert format_summary(None) == "No measurements recorded."


def test_summary_one_record_has_zero_slope():
    summary = calculate_trend([WeightEntry("2026-07-01", 122.0)])

    assert summary is not None
    assert summary.slope_kg_per_day == 0.0
    assert summary.slope_kg_per_week == 0.0
    assert "Measurements: 1" in format_summary(summary)


def test_regression_uses_recorded_dates_and_handles_missing_days():
    summary = calculate_trend(
        [
            WeightEntry("2026-07-01", 100.0),
            WeightEntry("2026-07-03", 104.0),
            WeightEntry("2026-07-06", 110.0),
        ]
    )

    assert summary is not None
    assert summary.first_date == "2026-07-01"
    assert summary.latest_date == "2026-07-06"
    assert summary.slope_kg_per_day == pytest.approx(2.0)
    assert summary.slope_kg_per_week == pytest.approx(14.0)
    assert summary.intercept == pytest.approx(100.0)


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
