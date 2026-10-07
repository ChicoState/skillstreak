# syntax=docker/dockerfile:1
FROM python:3.14.7-slim-bookworm AS builder

ENV PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1 \
    PYTHONDONTWRITEBYTECODE=1
WORKDIR /build

COPY requirements.runtime.txt ./
RUN python -m pip install --prefix=/install --requirement requirements.runtime.txt

FROM python:3.14.7-slim-bookworm AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app/src \
    PATH=/usr/local/bin:$PATH
WORKDIR /app

RUN apt-get update \
    && apt-get upgrade --yes \
    && apt-get install --yes --no-install-recommends libpq5 \
    && rm -rf /var/lib/apt/lists/* \
    && groupadd --gid 10001 app \
    && useradd --uid 10001 --gid app --create-home app
COPY --from=builder /install /usr/local
COPY --chown=app:app . .
RUN chown app:app /app
USER app

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
  CMD python -c "import os; from urllib.request import urlopen; urlopen(f'http://127.0.0.1:{os.getenv(\"PORT\", \"8000\")}/healthz', timeout=2).read()"

CMD ["sh", "-c", "exec gunicorn --bind 0.0.0.0:${PORT:-8000} skillstreak.wsgi:application"]
