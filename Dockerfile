# ---------- Builder ----------
FROM python:3.13-slim AS builder

ENV PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN apt-get update && \
    apt-get install -y --no-install-recommends build-essential gcc libpq-dev curl ca-certificates && \
    rm -rf /var/lib/apt/lists/*

RUN python -m pip install --upgrade pip setuptools wheel poetry  \
    "poetry-plugin-export==1.8.0"

WORKDIR /app

COPY pyproject.toml poetry.lock* /app/

RUN poetry export -f requirements.txt --only main -o /app/requirements.txt && \
    pip wheel --no-cache-dir --wheel-dir /wheels -r /app/requirements.txt

COPY src/ /app/src/
COPY scripts/ /app/scripts/

# ---------- Runtime ----------
FROM python:3.13-slim AS runtime

RUN apt-get update && \
    apt-get install -y --no-install-recommends libpq5 tini && \
    rm -rf /var/lib/apt/lists/*

ENV PATH="/home/briefex/.local/bin:${PATH}" \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN useradd --create-home --shell /bin/bash briefex

WORKDIR /app

COPY --from=builder /wheels /wheels
COPY --from=builder /app/requirements.txt /app/requirements.txt

RUN python -m pip install --upgrade pip && \
    python -m pip install --no-index --find-links=/wheels -r /app/requirements.txt && \
    rm -rf /wheels

COPY --from=builder /app/src/ /app/src/
COPY --from=builder /app/scripts/ /app/scripts/

RUN chown -R briefex:briefex /app

USER briefex

ENTRYPOINT ["/usr/bin/tini", "--"]

CMD ["python", "-c", "import sys; print('Set CMD in compose (worker/beat)'); sys.exit(1)"]
