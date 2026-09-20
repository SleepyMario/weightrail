#!/usr/bin/env python3
from __future__ import annotations

import re
import sys
import tomllib
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent


def require_match(path: Path, pattern: str, expected: str, label: str) -> None:
    text = path.read_text(encoding="utf-8")
    match = re.search(pattern, text, flags=re.MULTILINE)
    actual = match.group(1) if match else None
    if actual != expected:
        raise SystemExit(
            f"{label} version mismatch: expected {expected!r}, found {actual!r}"
        )


def main() -> int:
    with (ROOT / "pyproject.toml").open("rb") as handle:
        version = tomllib.load(handle)["project"]["version"]

    if not re.fullmatch(r"[0-9]+\.[0-9]+\.[0-9]+", version):
        raise SystemExit(f"Release version must be numeric X.Y.Z, found {version!r}")

    require_match(
        ROOT / "debian" / "changelog",
        r"^weightrail \(([^)-]+)-[0-9]+\)",
        version,
        "Debian",
    )
    require_match(
        ROOT / "Dockerfile",
        r"^ARG WEIGHTRAIL_VERSION=([^\s]+)$",
        version,
        "Docker",
    )
    require_match(
        ROOT / "packaging" / "windows" / "Weightrail.nsi",
        r'^\s*!define VERSION "([^"]+)"$',
        version,
        "Windows",
    )

    ebuild = (
        ROOT
        / "gentoo"
        / "app-misc"
        / "weightrail"
        / f"weightrail-{version}.ebuild"
    )
    if not ebuild.is_file():
        raise SystemExit(f"Gentoo ebuild is missing: {ebuild.relative_to(ROOT)}")

    print(f"All package targets agree on Weightrail {version}.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
