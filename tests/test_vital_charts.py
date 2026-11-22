from datetime import date
import pytest


@pytest.fixture
def axes():
    matplotlib = pytest.importorskip('matplotlib')
    matplotlib.use('Agg')
    from matplotlib.figure import Figure
    return Figure().subplots()
from weightrail.db import VitalEntry
from weightrail.gui_chart import render_vital_chart
from weightrail.graph import render_vital_graph


def test_blood_pressure_orders_dates_and_keeps_both_series(axes):
    ax = axes
    render_vital_chart(ax, [VitalEntry('2026-10-10', 125, 82, 70), VitalEntry('2026-10-01', 120, 80, 65)], 'blood_pressure')
    assert ax.get_ylabel() == 'mmHg'
    assert [line.get_label() for line in ax.lines] == ['Systolic', 'Diastolic']
    assert list(ax.lines[0].get_xdata()) == [date(2026, 10, 1), date(2026, 10, 10)]
    assert list(ax.lines[0].get_ydata()) == [120, 125]
    assert list(ax.lines[1].get_ydata()) == [80, 82]


def test_heart_rate_single_point_and_empty_refresh(axes):
    ax = axes
    render_vital_chart(ax, [], 'heart_rate')
    assert not ax.axison
    render_vital_chart(ax, [VitalEntry('2026-10-01', 120, 80, 65)], 'heart_rate')
    assert ax.axison
    assert ax.get_ylabel() == 'bpm'
    assert len(ax.lines) == 1
    assert list(ax.lines[0].get_ydata()) == [65]
    render_vital_chart(ax, [], 'heart_rate')
    assert len(ax.lines) == 0


def test_terminal_vital_graphs_have_distinct_titles_and_empty_states():
    pytest.importorskip('plotext')
    entries = [VitalEntry('2026-10-01', 120, 80, 65)]
    assert 'Blood pressure' in render_vital_graph(entries, 'blood_pressure')
    assert 'Resting heart rate' in render_vital_graph(entries, 'heart_rate')
    assert 'No measurements' in render_vital_graph([], 'blood_pressure')
