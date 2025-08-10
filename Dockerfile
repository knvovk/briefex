FROM python:3.13-slim AS builder

ENV PIP_NO_CACHE_DIR=1
ENV POETRY_VERSION=1.8.3

RUN apt-get update && \
    apt-get install -y --no-install-recommends build-essential curl git libpq-dev && \
    rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir "poetry==${POETRY_VERSION}"

WORKDIR /app

COPY pyproject.toml poetry.lock* ./

RUN poetry export --only main -f requirements.txt \
    --output /tmp/requirements.txt --without-hashes

FROM python:3.13-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PIP_NO_CACHE_DIR=1
ENV PYTHONPATH=/app/src

RUN apt-get update && \
    apt-get install -y --no-install-recommends libpq5 && \
    rm -rf /var/lib/apt/lists/*

RUN useradd --create-home --uid 10001 appuser

WORKDIR /app

COPY --from=builder /tmp/requirements.txt /tmp/requirements.txt

RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r /tmp/requirements.txt

COPY src ./src
COPY scripts ./scripts

RUN chown -R appuser:appuser /app

USER appuser

CMD ["python", "-c", "print('briefex image ready; override CMD in compose')"]
