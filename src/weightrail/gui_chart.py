from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date

from .db import WeightEntry
from .stats import calculate_trend


@dataclass(frozen=True)
class ChartData:
    dates: tuple[date, ...]
    weights: tuple[float, ...]
    trend_weights: tuple[float, ...] | None


def prepare_chart_data(entries: Sequence[WeightEntry]) -> ChartData:
    """Prepare chronologically ordered, calendar-spaced values for the GUI chart."""
    ordered_entries = sorted(entries, key=lambda entry: date.fromisoformat(entry.date))
    if not ordered_entries:
        return ChartData(dates=(), weights=(), trend_weights=None)

    dates = tuple(date.fromisoformat(entry.date) for entry in ordered_entries)
    weights = tuple(entry.weight_kg for entry in ordered_entries)
    if len(ordered_entries) == 1:
        return ChartData(dates=dates, weights=weights, trend_weights=None)

    trend = calculate_trend(ordered_entries)
    assert trend is not None
    first_date = dates[0]
    trend_weights = tuple(
        trend.intercept + trend.slope_kg_per_day * (entry_date - first_date).days
        for entry_date in dates
    )
    return ChartData(dates=dates, weights=weights, trend_weights=trend_weights)


class WeightChart:
    """Small Matplotlib-backed GTK chart component."""

    def __init__(self, Figure, FigureCanvasGTK3Agg):
        self.figure = Figure(figsize=(7, 3), dpi=100)
        self.axes = self.figure.add_subplot(111)
        self.canvas = FigureCanvasGTK3Agg(self.figure)
        self.canvas.set_hexpand(True)
        self.canvas.set_vexpand(True)

    def refresh(self, entries: Sequence[WeightEntry]) -> None:
        from matplotlib import dates as mdates

        chart_data = prepare_chart_data(entries)
        self.axes.clear()
        self.axes.set_title("Weight")

        if not chart_data.dates:
            self.axes.text(
                0.5,
                0.5,
                "No measurements to graph.",
                horizontalalignment="center",
                verticalalignment="center",
                transform=self.axes.transAxes,
            )
            self.axes.set_axis_off()
            self.figure.tight_layout()
            self.canvas.draw_idle()
            return

        self.axes.set_axis_on()
        self.axes.plot(
            chart_data.dates,
            chart_data.weights,
            color="tab:blue",
            marker="o",
            linewidth=1.5,
            label="Measurements",
        )
        if chart_data.trend_weights is not None:
            self.axes.plot(
                chart_data.dates,
                chart_data.trend_weights,
                color="tab:orange",
                linestyle="--",
                linewidth=1.5,
                label="Linear trend",
            )
            self.axes.legend()

        locator = mdates.AutoDateLocator(minticks=3, maxticks=8)
        self.axes.xaxis.set_major_locator(locator)
        self.axes.xaxis.set_major_formatter(mdates.ConciseDateFormatter(locator))
        self.axes.set_xlabel("Date")
        self.axes.set_ylabel("kg")
        self.axes.grid(True, alpha=0.25)
        self.axes.margins(x=0.04)
        self.axes.tick_params(axis="x", labelrotation=30)
        self.figure.tight_layout()
        self.canvas.draw_idle()
