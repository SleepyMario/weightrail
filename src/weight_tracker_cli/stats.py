from __future__ import annotations

from dataclasses import dataclass
from datetime import date

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
