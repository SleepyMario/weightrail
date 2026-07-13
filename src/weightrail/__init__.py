"""SQLite-backed terminal weight tracker."""

from importlib.metadata import version


def get_version() -> str:
    return version("weightrail")
