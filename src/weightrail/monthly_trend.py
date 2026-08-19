"""Shared calendar-period aggregation and shape-preserving trend smoothing."""

from __future__ import annotations

import calendar
from collections import defaultdict
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from datetime import date

import numpy as np

from .dates import taipei_today
from .db import WeightEntry


PeriodKey = tuple[int, int]


@dataclass(frozen=True)
class SmoothedTrendData:
    aggregate_dates: tuple[date, ...]
    aggregate_means: tuple[float, ...]
    smoothed_dates: tuple[date, ...]
    smoothed_weights: tuple[float, ...]

    @property
    def monthly_dates(self) -> tuple[date, ...]:
        """Compatibility name for callers of the original monthly helper."""
        return self.aggregate_dates

    @property
    def monthly_means(self) -> tuple[float, ...]:
        """Compatibility name for callers of the original monthly helper."""
        return self.aggregate_means

    @property
    def weekly_dates(self) -> tuple[date, ...]:
        return self.aggregate_dates

    @property
    def weekly_means(self) -> tuple[float, ...]:
        return self.aggregate_means


MonthlyTrendData = SmoothedTrendData
WeeklyTrendData = SmoothedTrendData


def calculate_monthly_trend(
    entries: Sequence[WeightEntry],
    current_date: date | None = None,
) -> MonthlyTrendData | None:
    """Aggregate monthly means and return a conservative shape-preserving curve."""
    today = current_date or taipei_today()
    return _calculate_period_trend(entries, today, _month_key, _month_end)


def calculate_weekly_trend(
    entries: Sequence[WeightEntry],
    current_date: date | None = None,
) -> WeeklyTrendData | None:
    """Aggregate ISO-week means and return a conservative shape-preserving curve."""
    today = current_date or taipei_today()
    return _calculate_period_trend(entries, today, _iso_week_key, _iso_week_end)


def _calculate_period_trend(
    entries: Sequence[WeightEntry],
    today: date,
    key_for_date: Callable[[date], PeriodKey],
    period_end: Callable[[PeriodKey], date],
) -> SmoothedTrendData | None:
    grouped: dict[tuple[int, int], list[tuple[date, float]]] = defaultdict(list)
    for entry in entries:
        entry_date = date.fromisoformat(entry.date)
        if entry_date <= today:
            grouped[key_for_date(entry_date)].append((entry_date, entry.weight_kg))

    represented_periods = sorted(grouped)
    if len(represented_periods) < 2:
        return None
    # Visibility is delayed, but once eligible the first aggregate is retained.
    if today < period_end(represented_periods[1]):
        return None

    aggregate_points: list[tuple[date, float]] = []
    current_period = key_for_date(today)
    for period in represented_periods:
        measurements = grouped[period]
        end_date = period_end(period)
        is_incomplete_current_period = (
            period == current_period and today < end_date
        )
        point_date = (
            max(measurement_date for measurement_date, _weight in measurements)
            if is_incomplete_current_period
            else end_date
        )
        mean = sum(weight for _measurement_date, weight in measurements) / len(
            measurements
        )
        aggregate_points.append((point_date, mean))

    aggregate_dates = tuple(point[0] for point in aggregate_points)
    aggregate_means = tuple(point[1] for point in aggregate_points)
    smoothed_dates, smoothed_weights = _shape_preserving_curve(
        aggregate_dates, aggregate_means
    )
    return SmoothedTrendData(
        aggregate_dates=aggregate_dates,
        aggregate_means=aggregate_means,
        smoothed_dates=smoothed_dates,
        smoothed_weights=smoothed_weights,
    )


def _month_key(value: date) -> PeriodKey:
    return value.year, value.month


def _month_end(period: PeriodKey) -> date:
    year, month = period
    return date(year, month, calendar.monthrange(year, month)[1])


def _iso_week_key(value: date) -> PeriodKey:
    iso_date = value.isocalendar()
    return iso_date.year, iso_date.week


def _iso_week_end(period: PeriodKey) -> date:
    iso_year, iso_week = period
    return date.fromisocalendar(iso_year, iso_week, 7)


def _shape_preserving_curve(
    point_dates: tuple[date, ...],
    point_values: tuple[float, ...],
) -> tuple[tuple[date, ...], tuple[float, ...]]:
    if len(point_dates) == 1:
        return point_dates, point_values

    x = np.array([value.toordinal() for value in point_dates], dtype=float)
    y = np.array(point_values, dtype=float)
    sample_x = np.arange(int(x[0]), int(x[-1]) + 1, dtype=float)
    if len(point_dates) == 2:
        sample_y = np.interp(sample_x, x, y)
    else:
        derivatives = _pchip_derivatives(x, y)
        sample_y = np.empty_like(sample_x)
        for index in range(len(x) - 1):
            is_last = index == len(x) - 2
            mask = (sample_x >= x[index]) & (
                sample_x <= x[index + 1] if is_last else sample_x < x[index + 1]
            )
            interval_x = sample_x[mask]
            width = x[index + 1] - x[index]
            t = (interval_x - x[index]) / width
            sample_y[mask] = (
                (2 * t**3 - 3 * t**2 + 1) * y[index]
                + (t**3 - 2 * t**2 + t) * width * derivatives[index]
                + (-2 * t**3 + 3 * t**2) * y[index + 1]
                + (t**3 - t**2) * width * derivatives[index + 1]
            )

    return (
        tuple(date.fromordinal(int(value)) for value in sample_x),
        tuple(float(value) for value in sample_y),
    )


def _pchip_derivatives(x: np.ndarray, y: np.ndarray) -> np.ndarray:
    widths = np.diff(x)
    slopes = np.diff(y) / widths
    derivatives = np.zeros_like(y)

    for index in range(1, len(y) - 1):
        previous_slope = slopes[index - 1]
        next_slope = slopes[index]
        if previous_slope * next_slope <= 0:
            continue
        previous_weight = 2 * widths[index] + widths[index - 1]
        next_weight = widths[index] + 2 * widths[index - 1]
        derivatives[index] = (previous_weight + next_weight) / (
            previous_weight / previous_slope + next_weight / next_slope
        )

    derivatives[0] = _endpoint_derivative(
        widths[0], widths[1], slopes[0], slopes[1]
    )
    derivatives[-1] = _endpoint_derivative(
        widths[-1], widths[-2], slopes[-1], slopes[-2]
    )
    return derivatives


def _endpoint_derivative(
    adjacent_width: float,
    next_width: float,
    adjacent_slope: float,
    next_slope: float,
) -> float:
    derivative = (
        (2 * adjacent_width + next_width) * adjacent_slope
        - adjacent_width * next_slope
    ) / (adjacent_width + next_width)
    if np.sign(derivative) != np.sign(adjacent_slope):
        return 0.0
    if np.sign(adjacent_slope) != np.sign(next_slope) and abs(derivative) > abs(
        3 * adjacent_slope
    ):
        return float(3 * adjacent_slope)
    return float(derivative)
