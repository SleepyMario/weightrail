from __future__ import annotations

from datetime import date

from .db import WeightEntry


def render_graph(entries: list[WeightEntry]) -> str:
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
    plt.scatter(days, weights, marker="dot")
    plt.plot(days, weights)
    return plt.build()
