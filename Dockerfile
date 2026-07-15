FROM docker.io/library/python:3.12-slim@sha256:c3d81d25b3154142b0b42eb1e61300024426268edeb5b5a26dd7ddf64d9daf28 AS builder

WORKDIR /build

COPY pyproject.toml README.md LICENSE ./
COPY src ./src

RUN python -m pip wheel --no-cache-dir --wheel-dir /wheels .

RUN python -m pip install --no-cache-dir --no-compile --no-index \
        --find-links=/wheels --prefix=/install weightrail==0.2.0 \
    && rm -f /install/bin/weightrail-gui \
    && rm -f /install/lib/python3.12/site-packages/weightrail/gui.py \
    && sed -i '/^weightrail-gui = /d' \
        /install/lib/python3.12/site-packages/weightrail-0.2.0.dist-info/entry_points.txt \
    && sed -i '/weightrail\/gui.py/d' \
        /install/lib/python3.12/site-packages/weightrail-0.2.0.dist-info/RECORD \
    && find /install/lib/python3.12/site-packages/numpy \
        -type d -name tests -prune -exec rm -rf {} +

FROM docker.io/library/python:3.12-slim@sha256:c3d81d25b3154142b0b42eb1e61300024426268edeb5b5a26dd7ddf64d9daf28

LABEL org.opencontainers.image.title="Weightrail" \
      org.opencontainers.image.description="Local-first SQLite-backed terminal weight tracker" \
      org.opencontainers.image.version="0.2.0" \
      org.opencontainers.image.source="https://github.com/SleepyMario/weightrail" \
      org.opencontainers.image.licenses="MIT" \
      org.opencontainers.image.revision="a5bf34eb1dec403f20a0160137fb9253527eef16"

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
