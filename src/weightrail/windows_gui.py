from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence
from pathlib import Path

from .dates import taipei_today
from .db import (
    DEFAULT_DB_PATH,
    DatabaseError,
    connect,
    list_weights,
    migrate_legacy_database,
    parse_weight,
    upsert_weight,
)
from .gui_chart import (
    ALL_SERIES,
    LINEAR_TREND,
    MEASUREMENTS,
    MONTHLY_TREND,
    SERIES_LABELS,
    WEEKLY_TREND,
    chart_series_availability,
    prepare_chart_data,
)
from .stats import calculate_stats, format_optional_change, format_optional_weight


def load_desktop_modules():
    import tkinter as tk
    from tkinter import messagebox, ttk

    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
    from matplotlib.figure import Figure

    return tk, ttk, messagebox, Figure, FigureCanvasTkAgg


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Windows desktop frontend for Weightrail.")
    parser.add_argument("--db-path", default=str(DEFAULT_DB_PATH), help="SQLite database path")
    args = parser.parse_args(argv)

    try:
        tk, ttk, messagebox, Figure, FigureCanvasTkAgg = load_desktop_modules()
    except (ImportError, RuntimeError) as exc:
        print(
            "Error: the Weightrail Windows interface requires Tk and Matplotlib.",
            file=sys.stderr,
        )
        print(f"Details: {exc}", file=sys.stderr)
        return 1

    db_path = Path(args.db_path).expanduser()
    try:
        if db_path == DEFAULT_DB_PATH:
            migrate_legacy_database()
    except DatabaseError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    root = tk.Tk()
    root.title("Weightrail")
    root.geometry("900x900")
    root.minsize(680, 650)
    app = WeightrailWindowsApp(
        root,
        db_path,
        tk,
        ttk,
        messagebox,
        Figure,
        FigureCanvasTkAgg,
    )
    app.refresh()
    root.mainloop()
    return 0


class WeightrailWindowsApp:
    def __init__(
        self,
        root,
        db_path: Path,
        tk,
        ttk,
        messagebox,
        Figure,
        FigureCanvasTkAgg,
    ) -> None:
        self.root = root
        self.db_path = db_path
        self.tk = tk
        self.messagebox = messagebox
        self.visible = {series: tk.BooleanVar(value=True) for series in ALL_SERIES}

        style = ttk.Style(root)
        if "vista" in style.theme_names():
            style.theme_use("vista")
        style.configure("Title.TLabel", font=("Segoe UI", 20, "bold"))
        style.configure("Subtitle.TLabel", foreground="#666666")
        style.configure("Value.TLabel", font=("Segoe UI", 12, "bold"))

        outer = ttk.Frame(root, padding=20)
        outer.pack(fill="both", expand=True)
        ttk.Label(outer, text="Weightrail", style="Title.TLabel").pack(anchor="w")
        ttk.Label(
            outer,
            text="Weight tracking, kept simple",
            style="Subtitle.TLabel",
        ).pack(anchor="w", pady=(0, 14))

        entry_frame = ttk.LabelFrame(outer, text="Today's weight", padding=12)
        entry_frame.pack(fill="x", pady=(0, 12))
        self.weight = ttk.Entry(entry_frame, font=("Segoe UI", 12))
        self.weight.pack(side="left", fill="x", expand=True, padx=(0, 10))
        self.weight.bind("<Return>", self.record)
        ttk.Button(entry_frame, text="Record today", command=self.record).pack(side="right")

        self.status = ttk.Label(outer, text="", style="Subtitle.TLabel")
        self.status.pack(fill="x", pady=(0, 8))

        stats = ttk.LabelFrame(outer, text="At a glance", padding=12)
        stats.pack(fill="x", pady=(0, 12))
        self.stats_values = {}
        for column, key in enumerate(("Latest", "Previous", "Total", "7-day", "30-day", "Weekly slope")):
            cell = ttk.Frame(stats)
            cell.grid(row=0, column=column, sticky="ew", padx=6)
            ttk.Label(cell, text=key, style="Subtitle.TLabel").pack(anchor="w")
            value = ttk.Label(cell, text="n/a", style="Value.TLabel")
            value.pack(anchor="w")
            self.stats_values[key] = value
            stats.columnconfigure(column, weight=1)

        graph = ttk.LabelFrame(outer, text="Weight history", padding=8)
        graph.pack(fill="both", expand=True, pady=(0, 12))
        self.figure = Figure(figsize=(8, 4.2), dpi=100)
        self.axes = self.figure.add_subplot(111)
        self.canvas = FigureCanvasTkAgg(self.figure, master=graph)
        self.canvas.get_tk_widget().pack(fill="both", expand=True)

        controls = ttk.Frame(graph)
        controls.pack(fill="x", pady=(8, 0))
        self.line_controls = {}
        for series in ALL_SERIES:
            control = ttk.Checkbutton(
                controls,
                text=SERIES_LABELS[series],
                variable=self.visible[series],
                command=self.render_chart,
            )
            control.pack(side="left", padx=(0, 12))
            self.line_controls[series] = control

        recent = ttk.LabelFrame(outer, text="Recent entries", padding=8)
        recent.pack(fill="both")
        self.recent = ttk.Treeview(recent, columns=("date", "weight"), show="headings", height=7)
        self.recent.heading("date", text="Date")
        self.recent.heading("weight", text="Weight kg")
        self.recent.column("date", anchor="w")
        self.recent.column("weight", anchor="e", width=120)
        self.recent.pack(fill="both", expand=True)
        self.entries = []

    def record(self, _event=None) -> None:
        try:
            value = parse_weight(self.weight.get().strip())
            with connect(self.db_path) as connection:
                action = upsert_weight(connection, taipei_today().isoformat(), value)
            self.weight.delete(0, self.tk.END)
            self.status.configure(text=f"{action.capitalize()} today's weight: {value:.1f} kg")
            self.refresh()
        except (ValueError, DatabaseError) as exc:
            self.messagebox.showerror("Unable to record weight", str(exc), parent=self.root)

    def refresh(self) -> None:
        try:
            with connect(self.db_path) as connection:
                self.entries = list_weights(connection)
        except DatabaseError as exc:
            self.messagebox.showerror("Unable to read data", str(exc), parent=self.root)
            return

        stats = calculate_stats(self.entries)
        values = {
            "Latest": format_optional_weight(stats.latest_weight if stats else None),
            "Previous": format_optional_change(stats.change_since_previous if stats else None),
            "Total": format_optional_change(stats.total_change if stats else None),
            "7-day": format_optional_weight(stats.average_7_day if stats else None),
            "30-day": format_optional_weight(stats.average_30_day if stats else None),
            "Weekly slope": (
                f"{stats.slope_kg_per_week:+.3f} kg" if stats else "n/a"
            ),
        }
        for key, value in values.items():
            self.stats_values[key].configure(text=value)

        for item in self.recent.get_children():
            self.recent.delete(item)
        for entry in reversed(self.entries[-10:]):
            self.recent.insert("", "end", values=(entry.date, f"{entry.weight_kg:.1f}"))
        self.render_chart()

    def render_chart(self) -> None:
        from matplotlib import dates as mdates

        chart = prepare_chart_data(self.entries)
        available = chart_series_availability(chart)
        for series, control in self.line_controls.items():
            control.configure(state="normal" if available[series] else "disabled")

        axes = self.axes
        axes.clear()
        if not chart.dates:
            axes.text(0.5, 0.5, "No measurements to graph.", ha="center", va="center", transform=axes.transAxes)
            axes.set_axis_off()
            self.canvas.draw_idle()
            return

        axes.set_axis_on()
        if self.visible[MEASUREMENTS].get():
            axes.plot(chart.dates, chart.weights, color="#4f8cff", marker="o", linewidth=1.6, label=SERIES_LABELS[MEASUREMENTS])
        if self.visible[LINEAR_TREND].get() and chart.trend_weights is not None:
            axes.plot(chart.dates, chart.trend_weights, color="#ff9f43", linestyle="--", linewidth=1.5, label=SERIES_LABELS[LINEAR_TREND])
        if self.visible[WEEKLY_TREND].get() and chart.weekly_trend is not None:
            axes.plot(chart.weekly_trend.smoothed_dates, chart.weekly_trend.smoothed_weights, color="#9b59b6", linestyle=":", linewidth=1.8, label=SERIES_LABELS[WEEKLY_TREND])
        if self.visible[MONTHLY_TREND].get() and chart.monthly_trend is not None:
            axes.plot(chart.monthly_trend.smoothed_dates, chart.monthly_trend.smoothed_weights, color="#27ae60", linewidth=2, label=SERIES_LABELS[MONTHLY_TREND])

        locator = mdates.AutoDateLocator(minticks=3, maxticks=8)
        axes.xaxis.set_major_locator(locator)
        axes.xaxis.set_major_formatter(mdates.ConciseDateFormatter(locator))
        axes.set_ylabel("kg")
        axes.grid(True, alpha=0.25)
        axes.margins(x=0.04)
        handles, _labels = axes.get_legend_handles_labels()
        if len(handles) > 1:
            axes.legend(ncol=2, frameon=False)
        self.figure.tight_layout()
        self.canvas.draw_idle()


if __name__ == "__main__":
    raise SystemExit(main())
