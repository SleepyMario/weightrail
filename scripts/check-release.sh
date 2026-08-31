#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

if ! worktree_status="$(git status --short)"; then
  echo "Unable to inspect the Git worktree." >&2
  exit 1
fi

if [[ -n "$worktree_status" ]]; then
  echo "Git worktree is not clean." >&2
  printf '%s\n' "$worktree_status" >&2
  exit 1
fi

python -m compileall src
python -m pytest
rm -rf dist build *.egg-info src/*.egg-info
python -m build
python -m twine check dist/*

tmpdir="$(mktemp -d /tmp/weightrail-release-check-XXXXXX)"
trap 'rm -rf "$tmpdir"' EXIT

version="$(python -c 'import tomllib; print(tomllib.load(open("pyproject.toml", "rb"))["project"]["version"])')"

python -m venv "$tmpdir/wheel-venv"
"$tmpdir/wheel-venv/bin/python" -m pip install "dist/weightrail-${version}-py3-none-any.whl"
"$tmpdir/wheel-venv/bin/weightrail" --version
"$tmpdir/wheel-venv/bin/weightrail" --help >/dev/null
"$tmpdir/wheel-venv/bin/weightrail" --db-path "$tmpdir/wheel.sqlite" 123.4 >/dev/null
"$tmpdir/wheel-venv/bin/weightrail" --db-path "$tmpdir/wheel.sqlite" --show >/dev/null
"$tmpdir/wheel-venv/bin/weightrail" --db-path "$tmpdir/wheel.sqlite" --summary >/dev/null

python -m venv "$tmpdir/sdist-venv"
"$tmpdir/sdist-venv/bin/python" -m pip install "dist/weightrail-${version}.tar.gz"
"$tmpdir/sdist-venv/bin/weightrail" --version
"$tmpdir/sdist-venv/bin/weightrail" --db-path "$tmpdir/sdist.sqlite" 123.4 >/dev/null
"$tmpdir/sdist-venv/bin/weightrail" --db-path "$tmpdir/sdist.sqlite" --summary >/dev/null

tar -tzf "dist/weightrail-${version}.tar.gz"
python -m zipfile -l "dist/weightrail-${version}-py3-none-any.whl"

echo "Local release check passed. No tag, push, or publish was performed."
