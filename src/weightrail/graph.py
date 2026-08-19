from __future__ import annotations

from datetime import date

from .db import WeightEntry
from .monthly_trend import calculate_monthly_trend
from .stats import calculate_trend


def render_graph(
    entries: list[WeightEntry], current_date: date | None = None
) -> str:
    if not entries:
        return "No measurements to graph."

    try:
        import plotext as plt
    except ImportError:
        return "Terminal graph unavailable: install the optional 'plotext' dependency."

    first_date = date.fromisoformat(entries[0].date)
    days = [(date.fromisoformat(entry.date) - first_date).days for entry in entries]
    weights = [entry.weight_kg for entry in entries]

    plt.clear_figure()
    plt.plotsize(80, 20)
    plt.title("Weight")
    plt.xlabel("days since first entry")
    plt.ylabel("kg")
    plt.scatter(days, weights, marker="dot", label="Measurements")
    plt.plot(days, weights)

    if len(entries) >= 2:
        linear_trend = calculate_trend(entries)
        assert linear_trend is not None
        linear_weights = [
            linear_trend.intercept + linear_trend.slope_kg_per_day * day
            for day in days
        ]
        plt.plot(
            days,
            linear_weights,
            color="orange",
            label="Linear trend",
        )

    monthly_trend = calculate_monthly_trend(entries, current_date)
    if monthly_trend is not None:
        monthly_days = [
            (point_date - first_date).days
            for point_date in monthly_trend.smoothed_dates
        ]
        plt.plot(
            monthly_days,
            list(monthly_trend.smoothed_weights),
            marker="braille",
            color="magenta",
            label="Monthly trend",
        )
    return plt.build()
