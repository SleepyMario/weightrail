import sys
from datetime import date
from types import SimpleNamespace

import pytest

from weightrail.db import WeightEntry
from weightrail.gui_chart import (
    MEASUREMENTS,
    MONTHLY_TREND,
    WEEKLY_TREND,
    WeightChart,
    prepare_chart_data,
)


def test_prepare_chart_data_handles_empty_entries():
    chart_data = prepare_chart_data([])

    assert chart_data.dates == ()
    assert chart_data.weights == ()
    assert chart_data.trend_weights is None


def test_prepare_chart_data_orders_entries_chronologically():
    chart_data = prepare_chart_data(
        [
            WeightEntry("2026-07-10", 101.0),
            WeightEntry("2026-07-01", 100.0),
            WeightEntry("2026-07-03", 102.0),
        ]
    )

    assert chart_data.dates == (
        date(2026, 7, 1),
        date(2026, 7, 3),
        date(2026, 7, 10),
    )
    assert chart_data.weights == (100.0, 102.0, 101.0)


def test_prepare_chart_data_keeps_one_point_without_trend():
    chart_data = prepare_chart_data([WeightEntry("2026-07-01", 122.0)])

    assert chart_data.dates == (date(2026, 7, 1),)
    assert chart_data.weights == (122.0,)
    assert chart_data.trend_weights is None


def test_prepare_chart_data_uses_actual_irregular_date_spacing_for_trend():
    chart_data = prepare_chart_data(
        [
            WeightEntry("2026-07-01", 100.0),
            WeightEntry("2026-07-03", 104.0),
            WeightEntry("2026-07-06", 110.0),
        ]
    )

    assert [(value - chart_data.dates[0]).days for value in chart_data.dates] == [0, 2, 5]
    assert chart_data.trend_weights == pytest.approx((100.0, 104.0, 110.0))


def test_prepare_chart_data_calculates_linear_trend_values():
    chart_data = prepare_chart_data(
        [
            WeightEntry("2026-07-01", 100.0),
            WeightEntry("2026-07-02", 103.0),
            WeightEntry("2026-07-04", 104.0),
        ]
    )

    assert chart_data.trend_weights is not None
    assert chart_data.trend_weights == pytest.approx(
        (100.7142857143, 101.9285714286, 104.3571428571)
    )


def test_prepare_chart_data_includes_shared_monthly_trend():
    chart_data = prepare_chart_data(
        [
            WeightEntry("2026-01-10", 100.0),
            WeightEntry("2026-02-10", 90.0),
            WeightEntry("2026-03-10", 80.0),
        ],
        current_date=date(2026, 4, 30),
    )

    assert chart_data.monthly_trend is not None
    assert chart_data.monthly_trend.aggregate_dates == (
        date(2026, 1, 31),
        date(2026, 2, 28),
        date(2026, 3, 31),
    )
    assert chart_data.monthly_trend.aggregate_means == (100.0, 90.0, 80.0)
    assert chart_data.weekly_trend is not None
    assert chart_data.weekly_trend.aggregate_dates == (
        date(2026, 1, 11),
        date(2026, 2, 15),
        date(2026, 3, 15),
    )


def test_weight_chart_renders_distinct_weekly_and_monthly_series(monkeypatch):
    plot_calls = []
    scatter_calls = []
    legend_labels = []

    class FakeLocator:
        def __init__(self, **_kwargs):
            pass

    class FakeAxis:
        def set_major_locator(self, _locator):
            pass

        def set_major_formatter(self, _formatter):
            pass

    class FakeAxes:
        def __init__(self):
            self.xaxis = FakeAxis()

        def clear(self):
            pass

        def set_title(self, _title):
            pass

        def set_axis_on(self):
            pass

        def plot(self, dates, weights, **kwargs):
            plot_calls.append((dates, weights, kwargs))

        def scatter(self, dates, weights, **kwargs):
            scatter_calls.append((dates, weights, kwargs))

        def legend(self, **kwargs):
            assert kwargs == {"ncol": 2}
            legend_labels.append(
                tuple(call[2]["label"] for call in plot_calls)
            )

        def set_xlabel(self, _label):
            pass

        def set_ylabel(self, _label):
            pass

        def grid(self, *_args, **_kwargs):
            pass

        def margins(self, **_kwargs):
            pass

        def tick_params(self, **_kwargs):
            pass

    fake_dates = SimpleNamespace(
        AutoDateLocator=FakeLocator,
        ConciseDateFormatter=lambda _locator: object(),
    )
    monkeypatch.setitem(sys.modules, "matplotlib", SimpleNamespace(dates=fake_dates))

    chart = WeightChart.__new__(WeightChart)
    chart.axes = FakeAxes()
    chart.figure = SimpleNamespace(tight_layout=lambda: None)
    chart.canvas = SimpleNamespace(draw_idle=lambda: None)
    chart_data = chart.refresh(
        [
            WeightEntry("2026-01-05", 100.0),
            WeightEntry("2026-02-02", 95.0),
            WeightEntry("2026-03-02", 90.0),
        ]
    )

    calls_by_label = {call[2].get("label"): call for call in plot_calls}
    assert calls_by_label["Weekly trend"][2] == {
        "color": "tab:purple",
        "linestyle": ":",
        "linewidth": 1.75,
        "label": "Weekly trend",
    }
    assert calls_by_label["Monthly trend"][2] == {
        "color": "tab:green",
        "linewidth": 2,
        "label": "Monthly trend",
    }
    assert {call[2]["marker"] for call in scatter_calls} == {"^", "s"}

    plot_calls.clear()
    scatter_calls.clear()
    chart.render(chart_data, {MEASUREMENTS, MONTHLY_TREND})
    assert [call[2]["label"] for call in plot_calls] == [
        "Measurements",
        "Monthly trend",
    ]
    assert legend_labels[-1] == ("Measurements", "Monthly trend")

    plot_calls.clear()
    scatter_calls.clear()
    chart.render(
        chart_data,
        {MEASUREMENTS, WEEKLY_TREND, MONTHLY_TREND},
    )
    assert [call[2]["label"] for call in plot_calls] == [
        "Measurements",
        "Weekly trend",
        "Monthly trend",
    ]
    assert legend_labels[-1] == (
        "Measurements",
        "Weekly trend",
        "Monthly trend",
    )
