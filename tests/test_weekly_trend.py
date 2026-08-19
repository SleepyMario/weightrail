from datetime import date

import pytest

from weightrail.db import WeightEntry
from weightrail.monthly_trend import calculate_weekly_trend


def test_week_one_alone_is_hidden():
    trend = calculate_weekly_trend(
        [WeightEntry("2026-01-05", 100.0)],
        date(2026, 1, 18),
    )

    assert trend is None


def test_week_two_is_hidden_before_sunday():
    trend = calculate_weekly_trend(
        [
            WeightEntry("2026-01-05", 100.0),
            WeightEntry("2026-01-12", 90.0),
        ],
        date(2026, 1, 16),
    )

    assert trend is None


def test_completed_second_week_reveals_both_weeks_retroactively():
    trend = calculate_weekly_trend(
        [
            WeightEntry("2026-01-05", 100.0),
            WeightEntry("2026-01-12", 90.0),
        ],
        date(2026, 1, 18),
    )

    assert trend is not None
    assert trend.aggregate_dates == (date(2026, 1, 11), date(2026, 1, 18))
    assert trend.aggregate_means == (100.0, 90.0)
    assert trend.smoothed_dates[0] == date(2026, 1, 11)
    assert trend.smoothed_dates[-1] == date(2026, 1, 18)


def test_three_weeks_include_current_incomplete_week():
    trend = calculate_weekly_trend(
        [
            WeightEntry("2026-01-05", 100.0),
            WeightEntry("2026-01-12", 95.0),
            WeightEntry("2026-01-19", 90.0),
            WeightEntry("2026-01-21", 88.0),
        ],
        date(2026, 1, 21),
    )

    assert trend is not None
    assert trend.aggregate_dates == (
        date(2026, 1, 11),
        date(2026, 1, 18),
        date(2026, 1, 21),
    )
    assert trend.aggregate_means == (100.0, 95.0, 89.0)


def test_weekly_mean_includes_monday_and_sunday_measurements():
    trend = calculate_weekly_trend(
        [
            WeightEntry("2026-01-05", 80.0),
            WeightEntry("2026-01-11", 100.0),
            WeightEntry("2026-01-12", 95.0),
            WeightEntry("2026-01-18", 85.0),
        ],
        date(2026, 1, 18),
    )

    assert trend is not None
    assert trend.aggregate_dates == (date(2026, 1, 11), date(2026, 1, 18))
    assert trend.aggregate_means == (90.0, 90.0)


def test_iso_week_year_rollover_uses_iso_year_identity():
    trend = calculate_weekly_trend(
        [
            WeightEntry("2025-12-29", 100.0),
            WeightEntry("2026-01-04", 98.0),
            WeightEntry("2026-01-05", 96.0),
        ],
        date(2026, 1, 11),
    )

    assert trend is not None
    assert trend.aggregate_dates == (date(2026, 1, 4), date(2026, 1, 11))
    assert trend.aggregate_means == (99.0, 96.0)


def test_current_incomplete_later_week_excludes_future_measurements():
    trend = calculate_weekly_trend(
        [
            WeightEntry("2026-01-05", 105.0),
            WeightEntry("2026-01-12", 100.0),
            WeightEntry("2026-01-19", 100.0),
            WeightEntry("2026-01-21", 80.0),
            WeightEntry("2026-01-23", 10.0),
            WeightEntry("2026-01-26", 1.0),
        ],
        date(2026, 1, 21),
    )

    assert trend is not None
    assert trend.aggregate_dates[-1] == date(2026, 1, 21)
    assert trend.aggregate_means == (105.0, 100.0, 90.0)
    assert trend.smoothed_dates[-1] == date(2026, 1, 21)


def test_weekly_output_is_chronological_for_unsorted_sparse_entries():
    trend = calculate_weekly_trend(
        [
            WeightEntry("2026-02-02", 90.0),
            WeightEntry("2026-01-05", 100.0),
            WeightEntry("2026-01-19", 95.0),
        ],
        date(2026, 2, 8),
    )

    assert trend is not None
    assert trend.aggregate_dates == (
        date(2026, 1, 11),
        date(2026, 1, 25),
        date(2026, 2, 8),
    )
    assert tuple(sorted(trend.smoothed_dates)) == trend.smoothed_dates


def test_weekly_curve_uses_real_spacing_and_preserves_aggregate_means():
    trend = calculate_weekly_trend(
        [
            WeightEntry("2026-01-05", 100.0),
            WeightEntry("2026-01-26", 90.0),
        ],
        date(2026, 2, 1),
    )

    assert trend is not None
    assert len(trend.smoothed_dates) == 22
    values_by_date = dict(
        zip(trend.smoothed_dates, trend.smoothed_weights, strict=True)
    )
    for point_date, mean in zip(
        trend.aggregate_dates, trend.aggregate_means, strict=True
    ):
        assert values_by_date[point_date] == pytest.approx(mean)
