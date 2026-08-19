from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence
from importlib import resources
from pathlib import Path

from .dates import taipei_today
from .db import (
    DEFAULT_DB_PATH,
    LEGACY_DB_PATH,
    DatabaseError,
    connect,
    list_weights,
    migrate_legacy_database,
    parse_weight,
    upsert_weight,
)
from .gui_chart import (
    ALL_SERIES,
    SERIES_LABELS,
    WeightChart,
    chart_series_availability,
    prepare_chart_data,
)
from .stats import WeightStats, calculate_stats, format_optional_change, format_optional_weight


RECENT_ENTRY_LIMIT = 10


def add_style_classes(widget, *class_names: str) -> None:
    context = widget.get_style_context()
    for class_name in class_names:
        context.add_class(class_name)


def install_stylesheet(Gtk, screen):
    provider = Gtk.CssProvider()
    css = resources.files("weightrail").joinpath("gui.css").read_bytes()
    provider.load_from_data(css)
    Gtk.StyleContext.add_provider_for_screen(
        screen,
        provider,
        Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION,
    )
    return provider


def load_gtk():
    import gi

    gi.require_version("Gtk", "3.0")
    from gi.repository import Gtk

    return Gtk


def load_chart_backend():
    from matplotlib.backends.backend_gtk3agg import FigureCanvasGTK3Agg
    from matplotlib.figure import Figure

    return Figure, FigureCanvasGTK3Agg


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Small GTK frontend for Weightrail.")
    parser.add_argument("--db-path", default=str(DEFAULT_DB_PATH), help="SQLite database path")
    args = parser.parse_args(argv)

    try:
        Gtk = load_gtk()
    except (ImportError, ValueError) as exc:
        print(
            "Error: GTK support requires PyGObject and GTK 3. "
            "Install the optional GUI dependencies for this package.",
            file=sys.stderr,
        )
        print(f"Details: {exc}", file=sys.stderr)
        return 1

    try:
        Figure, FigureCanvasGTK3Agg = load_chart_backend()
    except (ImportError, RuntimeError, ValueError) as exc:
        print(
            "Error: the Weightrail GUI requires Matplotlib with GTK 3 support. "
            "Install 'weightrail[gui]' with pip, or install your distribution's "
            "Matplotlib GTK 3 package.",
            file=sys.stderr,
        )
        print(f"Details: {exc}", file=sys.stderr)
        return 1

    db_path = Path(args.db_path).expanduser()
    try:
        if db_path == DEFAULT_DB_PATH and migrate_legacy_database():
            print(
                f"Copied existing Weightrail data from {LEGACY_DB_PATH} to {DEFAULT_DB_PATH}; "
                "the original was kept as a rollback copy.",
                file=sys.stderr,
            )
    except DatabaseError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    window = WeightrailWindow(Gtk, db_path, Figure, FigureCanvasGTK3Agg)
    window.connect("destroy", Gtk.main_quit)
    window.show_all()
    try:
        Gtk.main()
    except KeyboardInterrupt:
        Gtk.main_quit()
        return 130
    return 0


class LineVisibilityState:
    def __init__(self) -> None:
        self.available = {series: False for series in ALL_SERIES}
        self.selected = {series: False for series in ALL_SERIES}

    def update_availability(self, availability: dict[str, bool]) -> None:
        for series in ALL_SERIES:
            was_available = self.available[series]
            is_available = availability[series]
            self.available[series] = is_available
            if not is_available:
                self.selected[series] = False
            elif not was_available:
                self.selected[series] = True

    def set_selected(self, series: str, selected: bool) -> None:
        self.selected[series] = bool(selected and self.available[series])

    @property
    def visible_series(self) -> frozenset[str]:
        return frozenset(
            series
            for series in ALL_SERIES
            if self.available[series] and self.selected[series]
        )


class WeightrailWindow:
    def __init__(self, Gtk, db_path: Path, Figure, FigureCanvasGTK3Agg):
        self.Gtk = Gtk
        self.db_path = db_path
        self.window = Gtk.Window(title="Weightrail")
        self.window.set_default_size(840, 880)
        self.window.set_size_request(420, 560)
        add_style_classes(self.window, "weightrail-window")
        self.css_provider = install_stylesheet(Gtk, self.window.get_screen())

        header = Gtk.HeaderBar()
        header.set_title("Weightrail")
        header.set_subtitle("Weight tracking, kept simple")
        header.set_show_close_button(True)
        add_style_classes(header, "app-header")
        self.window.set_titlebar(header)

        page = Gtk.ScrolledWindow()
        page.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        page.set_shadow_type(Gtk.ShadowType.NONE)
        self.window.add(page)

        root = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=16)
        root.set_margin_top(20)
        root.set_margin_bottom(20)
        root.set_margin_start(20)
        root.set_margin_end(20)
        add_style_classes(root, "weightrail-content")
        page.add(root)

        entry_card = self.create_card(
            "Today's weight",
            "Record or update today's measurement.",
        )
        root.pack_start(entry_card, False, False, 0)

        entry_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        entry_card.pack_start(entry_row, False, False, 0)

        self.weight_entry = Gtk.Entry()
        self.weight_entry.set_placeholder_text("Weight in kg")
        self.weight_entry.set_input_purpose(Gtk.InputPurpose.NUMBER)
        self.weight_entry.connect("activate", self.on_record_clicked)
        add_style_classes(self.weight_entry, "weight-entry")
        entry_row.pack_start(self.weight_entry, True, True, 0)

        self.record_button = Gtk.Button(label="Record today")
        self.record_button.connect("clicked", self.on_record_clicked)
        add_style_classes(self.record_button, "suggested-action", "primary-action")
        entry_row.pack_start(self.record_button, False, False, 0)

        self.status_label = Gtk.Label()
        self.status_label.set_xalign(0)
        self.status_label.set_line_wrap(True)
        add_style_classes(self.status_label, "status-label")
        entry_card.pack_start(self.status_label, False, False, 0)

        stats_card = self.create_card("At a glance")
        root.pack_start(stats_card, False, False, 0)
        self.stats_grid = Gtk.Grid(column_spacing=28, row_spacing=10)
        self.stats_grid.set_hexpand(True)
        add_style_classes(self.stats_grid, "stats-grid")
        stats_card.pack_start(self.stats_grid, False, False, 0)

        graph_card = self.create_card(
            "Weight history",
            "Measurements and trends over time.",
            "graph-card",
        )
        root.pack_start(graph_card, True, True, 0)

        self.line_visibility = LineVisibilityState()
        self.line_controls = {}
        self._syncing_line_controls = False

        self.weight_chart = WeightChart(Figure, FigureCanvasGTK3Agg)
        add_style_classes(self.weight_chart.canvas, "chart-canvas")
        graph_card.pack_start(self.weight_chart.canvas, True, True, 0)

        self.lines_expander = Gtk.Expander(label="Lines")
        self.lines_expander.set_expanded(False)
        add_style_classes(self.lines_expander, "lines-expander")
        graph_card.pack_start(self.lines_expander, False, False, 0)
        lines_box = Gtk.FlowBox()
        lines_box.set_selection_mode(Gtk.SelectionMode.NONE)
        lines_box.set_row_spacing(4)
        lines_box.set_column_spacing(12)
        lines_box.set_min_children_per_line(1)
        lines_box.set_max_children_per_line(4)
        lines_box.set_margin_top(4)
        lines_box.set_margin_bottom(2)
        self.lines_expander.add(lines_box)
        for series in ALL_SERIES:
            control = Gtk.CheckButton(label=SERIES_LABELS[series])
            control.connect("toggled", self.on_line_toggled, series)
            add_style_classes(control, "line-toggle")
            lines_box.add(control)
            self.line_controls[series] = control

        recent_card = self.create_card(
            "Recent entries",
            "Your latest measurements.",
            "recent-card",
        )
        root.pack_start(recent_card, False, False, 0)
        self.recent_store = Gtk.ListStore(str, str)
        self.recent_view = Gtk.TreeView(model=self.recent_store)
        self.recent_view.set_headers_visible(True)
        add_style_classes(self.recent_view, "recent-table")
        for index, title_text in enumerate(("Date", "Weight kg")):
            renderer = Gtk.CellRendererText()
            if index == 1:
                renderer.set_property("xalign", 1.0)
            column = Gtk.TreeViewColumn(title_text, renderer, text=index)
            column.set_expand(index == 0)
            self.recent_view.append_column(column)

        recent_scroll = Gtk.ScrolledWindow()
        recent_scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        recent_scroll.set_shadow_type(Gtk.ShadowType.NONE)
        recent_scroll.set_min_content_height(150)
        recent_scroll.set_max_content_height(210)
        recent_scroll.set_propagate_natural_height(True)
        add_style_classes(recent_scroll, "recent-scroll")
        recent_scroll.add(self.recent_view)
        recent_card.pack_start(recent_scroll, False, False, 0)

        self.refresh()

    def __getattr__(self, name: str):
        return getattr(self.window, name)

    def create_card(
        self,
        title_text: str,
        subtitle_text: str | None = None,
        *extra_classes: str,
    ):
        card = self.Gtk.Box(orientation=self.Gtk.Orientation.VERTICAL, spacing=10)
        add_style_classes(card, "card", *extra_classes)

        heading = self.Gtk.Label(label=title_text)
        heading.set_xalign(0)
        add_style_classes(heading, "section-title")
        card.pack_start(heading, False, False, 0)

        if subtitle_text is not None:
            subtitle = self.Gtk.Label(label=subtitle_text)
            subtitle.set_xalign(0)
            subtitle.set_line_wrap(True)
            add_style_classes(subtitle, "section-subtitle")
            card.pack_start(subtitle, False, False, 0)

        return card

    def on_record_clicked(self, *_args) -> None:
        raw_weight = self.weight_entry.get_text().strip()
        try:
            weight = parse_weight(raw_weight)
            today = taipei_today().isoformat()
            with connect(self.db_path) as connection:
                action = upsert_weight(connection, today, weight)
            self.weight_entry.set_text("")
            self.status_label.set_text(f"{action.title()} {weight:.1f} kg for {today}.")
            self.refresh()
        except (DatabaseError, ValueError) as exc:
            self.status_label.set_text(f"Error: {exc}")

    def refresh(self) -> None:
        try:
            with connect(self.db_path) as connection:
                entries = list_weights(connection)
        except DatabaseError as exc:
            self.status_label.set_text(f"Error: {exc}")
            entries = []

        self.refresh_stats(calculate_stats(entries))
        self.refresh_chart(entries)
        self.refresh_recent(entries)
        if not entries and not self.status_label.get_text():
            self.status_label.set_text("No measurements yet. Enter today's weight to begin.")

    def refresh_chart(self, entries) -> None:
        self.chart_data = prepare_chart_data(entries)
        self.line_visibility.update_availability(
            chart_series_availability(self.chart_data)
        )
        self.sync_line_controls()
        self.weight_chart.render(
            self.chart_data,
            self.line_visibility.visible_series,
        )

    def sync_line_controls(self) -> None:
        self._syncing_line_controls = True
        try:
            for series, control in self.line_controls.items():
                control.set_sensitive(self.line_visibility.available[series])
                control.set_active(self.line_visibility.selected[series])
        finally:
            self._syncing_line_controls = False

    def on_line_toggled(self, control, series: str) -> None:
        if self._syncing_line_controls:
            return
        self.line_visibility.set_selected(series, control.get_active())
        self.weight_chart.render(
            self.chart_data,
            self.line_visibility.visible_series,
        )

    def refresh_stats(self, stats: WeightStats | None) -> None:
        for child in self.stats_grid.get_children():
            self.stats_grid.remove(child)

        if stats is None:
            self.add_stat_row(0, "Status", "No measurements recorded.")
            return

        rows = [
            ("Latest", f"{stats.latest_weight:.1f} kg"),
            ("Change since previous", format_optional_change(stats.change_since_previous)),
            ("Total change", f"{stats.total_change:+.1f} kg"),
            ("7-day average", format_optional_weight(stats.average_7_day)),
            ("30-day average", format_optional_weight(stats.average_30_day)),
            ("Highest", f"{stats.highest_weight:.1f} kg on {stats.highest_date}"),
            ("Lowest", f"{stats.lowest_weight:.1f} kg on {stats.lowest_date}"),
            ("Entries", str(stats.entries)),
            ("Trend", f"{stats.slope_kg_per_day:+.4f} kg/day"),
            ("Trend", f"{stats.slope_kg_per_week:+.4f} kg/week"),
        ]
        for row_index, (label, value) in enumerate(rows):
            self.add_stat_row(row_index, label, value)

    def add_stat_row(self, row: int, label_text: str, value_text: str) -> None:
        label = self.Gtk.Label(label=label_text)
        label.set_xalign(0)
        value = self.Gtk.Label(label=value_text)
        value.set_xalign(1)
        value.set_hexpand(True)
        if label_text == "Latest":
            add_style_classes(label, "primary-stat-label")
            add_style_classes(value, "primary-stat-value")
        else:
            add_style_classes(label, "stat-label")
            add_style_classes(value, "stat-value")
        self.stats_grid.attach(label, 0, row, 1, 1)
        self.stats_grid.attach(value, 1, row, 1, 1)

    def refresh_recent(self, entries) -> None:
        self.recent_store.clear()
        for entry in reversed(entries[-RECENT_ENTRY_LIMIT:]):
            self.recent_store.append([entry.date, f"{entry.weight_kg:.1f}"])


if __name__ == "__main__":
    raise SystemExit(main())
