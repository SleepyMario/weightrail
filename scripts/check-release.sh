#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

if [[ -n "$(git status --short)" ]]; then
  echo "Git worktree is not clean." >&2
  git status --short >&2
  exit 1
fi

python -m compileall src
python -m pytest
rm -rf dist build *.egg-info src/*.egg-info
python -m build
python -m twine check dist/*

tmpdir="$(mktemp -d /tmp/weight-tracker-release-check-XXXXXX)"
trap 'rm -rf "$tmpdir"' EXIT

python -m venv "$tmpdir/wheel-venv"
"$tmpdir/wheel-venv/bin/python" -m pip install dist/weight_tracker_cli-0.1.0-py3-none-any.whl
"$tmpdir/wheel-venv/bin/weight-tracker" --version
"$tmpdir/wheel-venv/bin/weight-tracker" --help >/dev/null
"$tmpdir/wheel-venv/bin/weight-tracker" --db-path "$tmpdir/wheel.sqlite" 123.4 >/dev/null
"$tmpdir/wheel-venv/bin/weight-tracker" --db-path "$tmpdir/wheel.sqlite" --show >/dev/null
"$tmpdir/wheel-venv/bin/weight-tracker" --db-path "$tmpdir/wheel.sqlite" --summary >/dev/null

python -m venv "$tmpdir/sdist-venv"
"$tmpdir/sdist-venv/bin/python" -m pip install dist/weight_tracker_cli-0.1.0.tar.gz
"$tmpdir/sdist-venv/bin/weight-tracker" --version
"$tmpdir/sdist-venv/bin/weight-tracker" --db-path "$tmpdir/sdist.sqlite" 123.4 >/dev/null
"$tmpdir/sdist-venv/bin/weight-tracker" --db-path "$tmpdir/sdist.sqlite" --summary >/dev/null

tar -tzf dist/weight_tracker_cli-0.1.0.tar.gz
python -m zipfile -l dist/weight_tracker_cli-0.1.0-py3-none-any.whl

echo "Local release check passed. No tag, push, or publish was performed."
