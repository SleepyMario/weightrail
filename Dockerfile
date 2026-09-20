ARG WEIGHTRAIL_VERSION=0.3.1
ARG VCS_REF=unknown

FROM docker.io/library/python:3.12-slim@sha256:c3d81d25b3154142b0b42eb1e61300024426268edeb5b5a26dd7ddf64d9daf28 AS builder

WORKDIR /build

COPY pyproject.toml README.md LICENSE ./
COPY src ./src

RUN python -m pip wheel --no-cache-dir --wheel-dir /wheels .

RUN python -m pip install --no-cache-dir --no-compile --no-index \
        --find-links=/wheels --prefix=/install weightrail \
    && rm -f /install/bin/weightrail-gui \
    && rm -f /install/lib/python3.12/site-packages/weightrail/gui.py \
    && dist_info="$(find /install/lib/python3.12/site-packages -maxdepth 1 \
        -type d -name 'weightrail-*.dist-info' -print -quit)" \
    && test -n "$dist_info" \
    && sed -i '/^weightrail-gui = /d' \
        "$dist_info/entry_points.txt" \
    && sed -i '/weightrail\/gui.py/d' \
        "$dist_info/RECORD" \
    && find /install/lib/python3.12/site-packages/numpy \
        -type d -name tests -prune -exec rm -rf {} +

FROM docker.io/library/python:3.12-slim@sha256:c3d81d25b3154142b0b42eb1e61300024426268edeb5b5a26dd7ddf64d9daf28

ARG WEIGHTRAIL_VERSION
ARG VCS_REF

LABEL org.opencontainers.image.title="Weightrail" \
      org.opencontainers.image.description="Local-first SQLite-backed terminal weight tracker" \
      org.opencontainers.image.source="https://github.com/SleepyMario/weightrail" \
      org.opencontainers.image.version="${WEIGHTRAIL_VERSION}" \
      org.opencontainers.image.revision="${VCS_REF}" \
      org.opencontainers.image.licenses="MIT"

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    HOME=/home/weightrail

RUN groupadd --gid 1000 weightrail \
    && useradd --uid 1000 --gid 1000 --create-home --shell /usr/sbin/nologin weightrail \
    && install -d -o weightrail -g weightrail /data \
    && rm -rf /var/lib/apt/lists/* /var/cache/apt/*

COPY --from=builder /install/ /usr/local/

COPY LICENSE /usr/share/licenses/weightrail/LICENSE
COPY README.md CHANGELOG.md /usr/share/doc/weightrail/

WORKDIR /data
USER 1000:1000

ENTRYPOINT ["weightrail"]
