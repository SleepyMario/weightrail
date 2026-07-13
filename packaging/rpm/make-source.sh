#!/usr/bin/env bash
set -euo pipefail

root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
version="$(sed -n 's/^version = "\([^"]*\)"/\1/p' "$root/pyproject.toml")"

if [[ -z "$version" ]]; then
    echo "Unable to read the project version from pyproject.toml" >&2
    exit 1
fi
if [[ $# -ne 1 ]]; then
    echo "usage: $0 OUTPUT-DIRECTORY" >&2
    exit 2
fi

output_dir="$(mkdir -p "$1" && cd "$1" && pwd)"
archive="$output_dir/weight-tracker-cli-$version.tar.gz"
epoch="${SOURCE_DATE_EPOCH:-$(git -C "$root" log -1 --format=%ct)}"
stage="$(mktemp -d "${TMPDIR:-/tmp}/weightrail-rpm-source.XXXXXX")"
trap 'rm -rf "$stage"' EXIT

topdir="$stage/weight-tracker-cli-$version"
mkdir -p "$topdir/packaging/rpm"
cp -a \
    "$root/CHANGELOG.md" \
    "$root/LICENSE" \
    "$root/MANIFEST.in" \
    "$root/README.md" \
    "$root/pyproject.toml" \
    "$root/src" \
    "$root/tests" \
    "$topdir/"
cp -a \
    "$root/packaging/rpm/README.md" \
    "$root/packaging/rpm/make-source.sh" \
    "$root/packaging/rpm/weightrail.spec" \
    "$topdir/packaging/rpm/"

find "$topdir" -type d \( \
    -name __pycache__ -o \
    -name .pytest_cache -o \
    -name '*.egg-info' \
    \) -prune -exec rm -rf {} +
find "$topdir" -type f \( -name '*.pyc' -o -name '*.pyo' \) -delete
find "$topdir" -type d -exec chmod 0755 {} +
find "$topdir" -type f -exec chmod 0644 {} +
chmod 0755 "$topdir/packaging/rpm/make-source.sh"

tar \
    --sort=name \
    --mtime="@$epoch" \
    --owner=0 \
    --group=0 \
    --numeric-owner \
    --format=gnu \
    -C "$stage" \
    -cf - "weight-tracker-cli-$version" | gzip -n >"$archive"

printf '%s\n' "$archive"
