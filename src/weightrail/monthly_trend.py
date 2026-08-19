from __future__ import annotations

import calendar
from collections import defaultdict
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date

import numpy as np

from .dates import taipei_today
from .db import WeightEntry


@dataclass(frozen=True)
class MonthlyTrendData:
    monthly_dates: tuple[date, ...]
    monthly_means: tuple[float, ...]
    smoothed_dates: tuple[date, ...]
    smoothed_weights: tuple[float, ...]


def calculate_monthly_trend(
    entries: Sequence[WeightEntry],
    current_date: date | None = None,
) -> MonthlyTrendData | None:
    """Aggregate monthly means and return a conservative shape-preserving curve."""
    today = current_date or taipei_today()
    grouped: dict[tuple[int, int], list[tuple[date, float]]] = defaultdict(list)
    for entry in entries:
        entry_date = date.fromisoformat(entry.date)
        if entry_date <= today:
            grouped[(entry_date.year, entry_date.month)].append(
                (entry_date, entry.weight_kg)
            )

    represented_months = sorted(grouped)
    if len(represented_months) < 2:
        return None

    monthly_points: list[tuple[date, float]] = []
    for year, month in represented_months:
        measurements = grouped[(year, month)]
        month_end = date(year, month, calendar.monthrange(year, month)[1])
        is_incomplete_current_month = (
            (year, month) == (today.year, today.month) and today < month_end
        )
        point_date = (
            max(measurement_date for measurement_date, _weight in measurements)
            if is_incomplete_current_month
            else month_end
        )
        mean = sum(weight for _measurement_date, weight in measurements) / len(
            measurements
        )
        monthly_points.append((point_date, mean))

    visible_points = monthly_points[1:]
    monthly_dates = tuple(point[0] for point in visible_points)
    monthly_means = tuple(point[1] for point in visible_points)
    smoothed_dates, smoothed_weights = _shape_preserving_curve(
        monthly_dates, monthly_means
    )
    return MonthlyTrendData(
        monthly_dates=monthly_dates,
        monthly_means=monthly_means,
        smoothed_dates=smoothed_dates,
        smoothed_weights=smoothed_weights,
    )


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
