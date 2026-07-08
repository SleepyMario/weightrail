from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta

import numpy as np

from .db import WeightEntry


@dataclass(frozen=True)
class TrendSummary:
    first_date: str
    latest_date: str
    measurements: int
    start_weight: float
    latest_weight: float
    net_change: float
    slope_kg_per_day: float
    slope_kg_per_week: float
    intercept: float


@dataclass(frozen=True)
class WeightStats:
    first_date: str
    latest_date: str
    entries: int
    latest_weight: float
    previous_weight: float | None
    change_since_previous: float | None
    total_change: float
    average_7_day: float | None
    average_30_day: float | None
    highest_date: str
    highest_weight: float
    lowest_date: str
    lowest_weight: float
    missing_days: int
    slope_kg_per_day: float
    slope_kg_per_week: float


def calculate_trend(entries: list[WeightEntry]) -> TrendSummary | None:
    if not entries:
        return None

    first = entries[0]
    latest = entries[-1]
    first_date = date.fromisoformat(first.date)
    days = np.array(
        [(date.fromisoformat(entry.date) - first_date).days for entry in entries],
        dtype=float,
    )
    weights = np.array([entry.weight_kg for entry in entries], dtype=float)

    if len(entries) == 1:
        slope = 0.0
        intercept = weights[0]
    else:
        slope, intercept = np.polyfit(days, weights, deg=1)

    return TrendSummary(
        first_date=first.date,
        latest_date=latest.date,
        measurements=len(entries),
        start_weight=first.weight_kg,
        latest_weight=latest.weight_kg,
        net_change=latest.weight_kg - first.weight_kg,
        slope_kg_per_day=float(slope),
        slope_kg_per_week=float(slope * 7),
        intercept=float(intercept),
    )


def calculate_stats(entries: list[WeightEntry]) -> WeightStats | None:
    if not entries:
        return None

    trend = calculate_trend(entries)
    assert trend is not None

    first = entries[0]
    latest = entries[-1]
    previous = entries[-2] if len(entries) > 1 else None
    highest = max(entries, key=lambda entry: entry.weight_kg)
    lowest = min(entries, key=lambda entry: entry.weight_kg)
    first_date = date.fromisoformat(first.date)
    latest_date = date.fromisoformat(latest.date)
    expected_days = (latest_date - first_date).days + 1

    return WeightStats(
        first_date=first.date,
        latest_date=latest.date,
        entries=len(entries),
        latest_weight=latest.weight_kg,
        previous_weight=previous.weight_kg if previous else None,
        change_since_previous=latest.weight_kg - previous.weight_kg if previous else None,
        total_change=latest.weight_kg - first.weight_kg,
        average_7_day=window_average(entries, latest_date, 7),
        average_30_day=window_average(entries, latest_date, 30),
        highest_date=highest.date,
        highest_weight=highest.weight_kg,
        lowest_date=lowest.date,
        lowest_weight=lowest.weight_kg,
        missing_days=max(0, expected_days - len(entries)),
        slope_kg_per_day=trend.slope_kg_per_day,
        slope_kg_per_week=trend.slope_kg_per_week,
    )


def window_average(entries: list[WeightEntry], latest_date: date, days: int) -> float | None:
    start = latest_date - timedelta(days=days - 1)
    window_entries = [
        entry
        for entry in entries
        if start <= date.fromisoformat(entry.date) <= latest_date
    ]
    if len(window_entries) < 2:
        return None
    return sum(entry.weight_kg for entry in window_entries) / len(window_entries)


def format_stats(stats: WeightStats | None) -> str:
    if stats is None:
        return "No measurements recorded."

    return "\n".join(
        [
            "Stats",
            f"Entries: {stats.entries}",
            f"First entry: {stats.first_date}",
            f"Latest entry: {stats.latest_date}",
            f"Latest weight: {stats.latest_weight:.1f} kg",
            f"Change since previous: {format_optional_change(stats.change_since_previous)}",
            f"Total change: {stats.total_change:+.1f} kg",
            f"7-day average: {format_optional_weight(stats.average_7_day)}",
            f"30-day average: {format_optional_weight(stats.average_30_day)}",
            f"Highest: {stats.highest_weight:.1f} kg on {stats.highest_date}",
            f"Lowest: {stats.lowest_weight:.1f} kg on {stats.lowest_date}",
            f"Missing days: {stats.missing_days}",
            f"Trend: {stats.slope_kg_per_day:+.4f} kg/day",
            f"Trend: {stats.slope_kg_per_week:+.4f} kg/week",
        ]
    )


def format_optional_change(value: float | None) -> str:
    if value is None:
        return "n/a"
    return f"{value:+.1f} kg"


def format_optional_weight(value: float | None) -> str:
    if value is None:
        return "n/a"
    return f"{value:.1f} kg"


def format_summary(summary: TrendSummary | None) -> str:
    if summary is None:
        return "No measurements recorded."

    return "\n".join(
        [
            "Summary",
            f"First date: {summary.first_date}",
            f"Latest date: {summary.latest_date}",
            f"Measurements: {summary.measurements}",
            f"Start weight: {summary.start_weight:.1f} kg",
            f"Latest weight: {summary.latest_weight:.1f} kg",
            f"Net change: {summary.net_change:+.1f} kg",
            f"Slope: {summary.slope_kg_per_day:+.4f} kg/day",
            f"Slope: {summary.slope_kg_per_week:+.4f} kg/week",
            f"Equation: w(d) ≈ {summary.slope_kg_per_day:.4f}d + {summary.intercept:.2f}",
            "where d = days since first recorded entry.",
        ]
    )
