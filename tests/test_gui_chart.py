from datetime import date

import pytest

from weightrail.db import WeightEntry
from weightrail.gui_chart import prepare_chart_data


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
    assert chart_data.monthly_trend.monthly_dates == (
        date(2026, 2, 28),
        date(2026, 3, 31),
    )
    assert chart_data.monthly_trend.monthly_means == (90.0, 80.0)
