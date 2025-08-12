# ==== Builder ====
FROM python:3.13-slim AS builder

ENV PIP_NO_CACHE_DIR=1 \
    POETRY_VERSION=1.8.3

RUN apt-get update && \
    apt-get install -y --no-install-recommends build-essential curl git libpq-dev && \
    rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir "poetry==${POETRY_VERSION}"

WORKDIR /app

COPY pyproject.toml poetry.lock* ./

RUN poetry export --only main -f requirements.txt \
    -o /tmp/requirements.txt --without-hashes

# ==== Runtime ====
FROM python:3.13-slim AS runtime

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

RUN apt-get update && \
    apt-get install -y --no-install-recommends libpq5 && \
    rm -rf /var/lib/apt/lists/*

RUN groupadd -g 10001 briefex && useradd -r -u 10001 -g briefex briefex

WORKDIR /app

COPY --from=builder /tmp/requirements.txt /tmp/requirements.txt
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r /tmp/requirements.txt

COPY --chown=briefex:briefex src ./src
COPY --chown=briefex:briefex scripts ./scripts

USER briefex

CMD ["python", "-c", "print('briefex image ready; override CMD in compose')"]
