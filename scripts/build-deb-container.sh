#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OUTPUT_DIR="${1:-$ROOT/dist/debian}"
IMAGE="${DEB_BUILD_IMAGE:-docker.io/library/ubuntu:24.04}"

mkdir -p "$OUTPUT_DIR"
OUTPUT_DIR="$(realpath "$OUTPUT_DIR")"

docker run --rm \
    -e DEBIAN_FRONTEND=noninteractive \
    -e HOST_UID="$(id -u)" \
    -e HOST_GID="$(id -g)" \
    -v "$ROOT:/source:ro" \
    -v "$OUTPUT_DIR:/out" \
    "$IMAGE" \
    bash -euo pipefail -c '
        apt-get update
        apt-get install -y --no-install-recommends \
            build-essential \
            debhelper \
            dh-python \
            devscripts \
            fakeroot \
            pybuild-plugin-pyproject \
            python3-all \
            python3-numpy \
            python3-pytest \
            python3-setuptools \
            python3-wheel
        mkdir -p /build
        cp -a /source /build/weightrail
        cd /build/weightrail
        dpkg-buildpackage --no-sign -b
        find /build -maxdepth 1 -type f \
            \( -name "*.deb" -o -name "*.buildinfo" -o -name "*.changes" \) \
            -exec cp -a {} /out/ \;
        chown -R "$HOST_UID:$HOST_GID" /out
    '

printf 'Debian artifacts: %s\n' "$OUTPUT_DIR"
