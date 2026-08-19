from datetime import date

import pytest

from weightrail.db import WeightEntry
from weightrail.monthly_trend import calculate_monthly_trend


def test_monthly_trend_requires_two_represented_months():
    assert calculate_monthly_trend([], date(2026, 4, 30)) is None
    assert (
        calculate_monthly_trend(
            [
                WeightEntry("2026-01-01", 100.0),
                WeightEntry("2026-01-31", 90.0),
            ],
            date(2026, 4, 30),
        )
        is None
    )


def test_exactly_two_months_starts_with_second_month_only():
    trend = calculate_monthly_trend(
        [
            WeightEntry("2026-01-15", 100.0),
            WeightEntry("2026-02-10", 90.0),
        ],
        date(2026, 4, 30),
    )

    assert trend is not None
    assert trend.monthly_dates == (date(2026, 2, 28),)
    assert trend.monthly_means == (90.0,)
    assert trend.smoothed_dates == trend.monthly_dates
    assert trend.smoothed_weights == trend.monthly_means


def test_three_months_continue_from_second_month():
    trend = calculate_monthly_trend(
        [
            WeightEntry("2026-01-15", 100.0),
            WeightEntry("2026-02-15", 95.0),
            WeightEntry("2026-03-15", 90.0),
        ],
        date(2026, 4, 30),
    )

    assert trend is not None
    assert trend.monthly_dates == (date(2026, 2, 28), date(2026, 3, 31))
    assert trend.monthly_means == (95.0, 90.0)
    assert trend.smoothed_dates[0] == date(2026, 2, 28)
    assert trend.smoothed_dates[-1] == date(2026, 3, 31)
    assert trend.smoothed_weights[0] == 95.0
    assert trend.smoothed_weights[-1] == 90.0


def test_monthly_mean_uses_every_measurement_in_the_month():
    trend = calculate_monthly_trend(
        [
            WeightEntry("2026-01-15", 110.0),
            WeightEntry("2026-02-01", 80.0),
            WeightEntry("2026-02-10", 90.0),
            WeightEntry("2026-02-27", 100.0),
        ],
        date(2026, 4, 30),
    )

    assert trend is not None
    assert trend.monthly_dates == (date(2026, 2, 28),)
    assert trend.monthly_means == (90.0,)


@pytest.mark.parametrize(
    ("year", "expected_month_end"),
    [(2025, date(2025, 2, 28)), (2024, date(2024, 2, 29))],
)
def test_february_month_end_handles_common_and_leap_years(
    year, expected_month_end
):
    trend = calculate_monthly_trend(
        [
            WeightEntry(f"{year}-01-10", 100.0),
            WeightEntry(f"{year}-02-10", 99.0),
        ],
        date(year, 3, 31),
    )

    assert trend is not None
    assert trend.monthly_dates == (expected_month_end,)


def test_current_incomplete_month_stops_at_latest_non_future_measurement():
    trend = calculate_monthly_trend(
        [
            WeightEntry("2026-07-15", 100.0),
            WeightEntry("2026-08-01", 100.0),
            WeightEntry("2026-08-10", 80.0),
            WeightEntry("2026-08-25", 10.0),
            WeightEntry("2026-09-01", 1.0),
        ],
        date(2026, 8, 19),
    )

    assert trend is not None
    assert trend.monthly_dates == (date(2026, 8, 10),)
    assert trend.monthly_means == (90.0,)
    assert max(trend.smoothed_dates) <= date(2026, 8, 19)


def test_monthly_output_is_chronological_for_unsorted_sparse_entries():
    trend = calculate_monthly_trend(
        [
            WeightEntry("2026-09-03", 90.0),
            WeightEntry("2026-01-05", 100.0),
            WeightEntry("2026-04-12", 95.0),
        ],
        date(2026, 12, 31),
    )

    assert trend is not None
    assert trend.monthly_dates == (date(2026, 4, 30), date(2026, 9, 30))
    assert tuple(sorted(trend.smoothed_dates)) == trend.smoothed_dates


def test_two_usable_sparse_points_fall_back_to_straight_interpolation():
    trend = calculate_monthly_trend(
        [
            WeightEntry("2026-01-05", 110.0),
            WeightEntry("2026-03-05", 100.0),
            WeightEntry("2026-09-05", 90.0),
        ],
        date(2026, 12, 31),
    )

    assert trend is not None
    midpoint_index = len(trend.smoothed_weights) // 2
    assert trend.smoothed_weights[midpoint_index] == pytest.approx(95.0, abs=0.05)


def test_shape_preserving_curve_does_not_overshoot_monthly_means():
    trend = calculate_monthly_trend(
        [
            WeightEntry("2026-01-10", 105.0),
            WeightEntry("2026-02-10", 100.0),
            WeightEntry("2026-03-10", 110.0),
            WeightEntry("2026-04-10", 101.0),
        ],
        date(2026, 6, 30),
    )

    assert trend is not None
    for start, end, low, high in (
        (date(2026, 2, 28), date(2026, 3, 31), 100.0, 110.0),
        (date(2026, 3, 31), date(2026, 4, 30), 101.0, 110.0),
    ):
        values = [
            weight
            for point_date, weight in zip(
                trend.smoothed_dates, trend.smoothed_weights, strict=True
            )
            if start <= point_date <= end
        ]
        assert min(values) >= low
        assert max(values) <= high


def test_smoothed_curve_passes_through_every_authoritative_monthly_mean():
    trend = calculate_monthly_trend(
        [
            WeightEntry("2026-01-10", 105.0),
            WeightEntry("2026-02-10", 100.0),
            WeightEntry("2026-03-10", 110.0),
            WeightEntry("2026-04-10", 101.0),
        ],
        date(2026, 6, 30),
    )

    assert trend is not None
    smoothed_points = dict(
        zip(trend.smoothed_dates, trend.smoothed_weights, strict=True)
    )
    for point_date, mean in zip(
        trend.monthly_dates, trend.monthly_means, strict=True
    ):
        assert smoothed_points[point_date] == pytest.approx(mean)
