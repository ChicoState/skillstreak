# syntax=docker/dockerfile:1
FROM python:3.14.7-slim-bookworm AS builder

ENV PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1 \
    PYTHONDONTWRITEBYTECODE=1
WORKDIR /build

COPY requirements.txt ./
RUN python -m pip install --prefix=/install --requirement requirements.txt

FROM python:3.14.7-slim-bookworm AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH=/usr/local/bin:$PATH
WORKDIR /app

RUN groupadd --gid 10001 app && useradd --uid 10001 --gid app --create-home app
COPY --from=builder /install /usr/local
COPY --chown=app:app . .
RUN chown app:app /app
USER app

EXPOSE 8000

# No CMD or HEALTHCHECK is intentionally defined. Those require the future Django
# project's application-owned ASGI/WSGI entrypoint and health route.
