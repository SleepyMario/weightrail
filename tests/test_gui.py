import pytest

from weightrail import gui


def test_gui_module_imports_without_loading_gtk():
    assert gui.RECENT_ENTRY_LIMIT == 10


def test_gui_help_does_not_require_display(capsys):
    with pytest.raises(SystemExit) as exc:
        gui.main(["--help"])

    captured = capsys.readouterr()
    assert exc.value.code == 0
    assert "Small GTK frontend" in captured.out
    assert "--db-path" in captured.out
