# Implementation Plan: SkillStreak Django Source Framework

## Status

Implemented — derived from the accepted
[`skillstreak-django-source-framework` specification](../specs/skillstreak-django-source-framework.md).

## Completion Record

The framework was delivered in the following pushed commits:

- `8f6dd10` — Django package, local settings, and liveness endpoint.
- `ad013e8` — secure production settings and their tests.
- `4db8b34` — Gunicorn runtime command, health check, and lockfile.
- `8d91b2f` — Docker Compose web workflow, documentation, and external-port
  regression coverage.

Final verification passed with six tests and 96.91% coverage, Ruff formatting
and lint checks, Django system checks, a host request to `/healthz`, and all
three required infrastructure smoke commands.

## Overview

Bootstrap the Docker-first Django project under `src/skillstreak`, with local
and production settings, a liveness-only `/healthz` endpoint, and a Cloud
Run-suitable Gunicorn image command. No product app, data model, migration,
authentication flow, or readiness endpoint is included.

## Architecture Decisions

- Use Django's conventional project package contents (`settings`, `urls`,
  `asgi`, and `wsgi`) under `src/skillstreak`; a project package may contain
  resources that are not tied to an application. Source:
  <https://docs.djangoproject.com/en/5.2/ref/applications/>.
- Keep `base`, `local`, and `production` settings separate. Production settings
  will be selected explicitly through `DJANGO_SETTINGS_MODULE` and verified
  with `check --deploy`, which Django recommends against the production
  settings file. Source:
  <https://docs.djangoproject.com/en/5.2/howto/deployment/checklist/>.
- Make `/healthz` liveness-only and use it for the container health check. It
  must not query PostgreSQL.
- Add Gunicorn as the production WSGI server. Django's development `runserver`
  is not intended for production. Source:
  <https://docs.djangoproject.com/en/5.2/howto/deployment/checklist/>.
- Make Compose wait for the existing PostgreSQL health check before starting
  the development web service, using `depends_on.condition: service_healthy`.
  Source: <https://docs.docker.com/compose/how-tos/startup-order/>.

## Dependency Graph

```text
pytest configuration + failing health test
            |
            v
project package + local settings
            |
            v
URL route + health view + ASGI/WSGI
            |
            +-------------------+
            v                   v
production settings          Docker/Gunicorn image
            |                   |
            +---------+---------+
                      v
              Compose web service
```

## Task List

### Task 1: Establish the failing health-check contract

**Description:** Configure pytest-django to load local settings from `src` and
add a test asserting that `/healthz` returns HTTP 200 with a minimal response.
Run it before project code exists to demonstrate the red state.

**Acceptance criteria:**

- [x] Pytest discovers Django tests from `src` using local settings.
- [x] The health-check test fails because the project implementation is absent.

**Verification:**

- [x] Build the current runtime image with
  `docker build --target runtime --tag skillstreak-framework-test .`, then run
  `docker run --rm --volume "$PWD:/app" --workdir /app skillstreak-framework-test pytest tests/application/test_health.py`.
  It fails for the expected missing-project behavior. Compose cannot run this
  test yet because the `web` service is created in Task 6.

**Dependencies:** None.

**Files likely touched:** `pyproject.toml`, `tests/application/test_health.py`.

### Task 2: Add the minimal project and local-settings foundation

**Description:** Create `manage.py`, the `skillstreak` package, and `base` /
`local` settings. Local settings use environment-based PostgreSQL configuration
and development-safe defaults; no migrations or domain apps are created.

**Acceptance criteria:**

- [x] `manage.py check` loads `skillstreak.settings.local`.
- [x] The local database configuration targets the Compose `db` host.
- [x] Configuration does not contain a real secret.

**Verification:**

- [x] `docker run --rm --volume "$PWD:/app" --workdir /app skillstreak-framework-test python manage.py diffsettings`
  loads the local settings successfully. Full `manage.py check` follows when
  the URL configuration exists in Task 3.
- [x] Ruff formatting and linting pass for the new files.

**Dependencies:** Task 1.

**Files likely touched:** `manage.py`, `src/skillstreak/__init__.py`,
`src/skillstreak/settings/__init__.py`, `src/skillstreak/settings/base.py`,
`src/skillstreak/settings/local.py`.

### Task 3: Implement the liveness route and application entrypoints

**Description:** Add the URL configuration, health view, ASGI, and WSGI
entrypoints. Make the Task 1 test green with the smallest HTTP response that
does not disclose configuration or query the database.

**Acceptance criteria:**

- [x] `GET /healthz` returns HTTP 200.
- [x] The response does not require a database connection.
- [x] Both ASGI and WSGI point to local settings by default.

**Verification:**

- [x] `docker run --rm --volume "$PWD:/app" --workdir /app skillstreak-framework-test pytest tests/application/test_health.py`
  passes.
- [x] `docker run --rm --volume "$PWD:/app" --workdir /app skillstreak-framework-test ruff format --check .`
  and `docker run --rm --volume "$PWD:/app" --workdir /app skillstreak-framework-test ruff check .`
  pass.

**Dependencies:** Task 2.

**Files likely touched:** `src/skillstreak/health.py`,
`src/skillstreak/urls.py`, `src/skillstreak/asgi.py`,
`src/skillstreak/wsgi.py`.

### Checkpoint: Application foundation

- [x] Health test passes after first failing.
- [x] `python manage.py check` passes in the web container.
- [x] Working changes are committed as an atomic application-foundation slice.

### Task 4: Add and test production settings

**Description:** Add `production.py` and focused tests for required
configuration. Require a production secret key, allowed hosts, and database
URL; configure HTTPS, proxy, secure-cookie, and HSTS protections appropriate
to a TLS-terminating Cloud Run deployment.

**Acceptance criteria:**

- [x] Production settings fail clearly when required values are absent.
- [x] With required values supplied, production settings load and
  `DEBUG=False`.
- [x] `check --deploy` runs against production settings in a controlled test
  environment.

**Verification:**

- [x] `docker run --rm --volume "$PWD:/app" --workdir /app skillstreak-framework-test pytest tests/application/test_production_settings.py`
  passes.
- [x] A `docker run` command with
  `DJANGO_SETTINGS_MODULE=skillstreak.settings.production` executes
  `python manage.py check --deploy` using non-secret test values.

**Dependencies:** Task 2.

**Files likely touched:** `src/skillstreak/settings/production.py`,
`tests/application/test_production_settings.py`.

### Task 5: Make the image production-runnable

**Description:** Add the approved Gunicorn dependency, regenerate the
pip-tools lockfile, and give the runtime image a non-root Gunicorn command and
liveness health check.

**Acceptance criteria:**

- [x] `requirements.in` and `requirements.txt` include Gunicorn.
- [x] The image starts Gunicorn on the Cloud Run `PORT` (falling back to 8000).
- [x] Docker's health check calls `/healthz` without requiring `curl`.

**Verification:**

- [x] Lockfile regeneration matches CI's pip-tools validation.
- [x] `./scripts/smoke-image.sh` builds the image and verifies its liveness
  endpoint.

**Dependencies:** Tasks 3 and 4.

**Files likely touched:** `requirements.in`, `requirements.txt`, `Dockerfile`,
`scripts/smoke-image.sh`.

### Task 6: Add the Docker Compose web workflow and update guidance

**Description:** Add the `web` Compose service with a source bind mount,
development command, configurable application port, environment forwarding,
and a database-health dependency. Update templates and onboarding commands.

**Acceptance criteria:**

- [x] `docker compose up --build` starts database then web service.
- [x] `curl --fail http://localhost:${APP_PORT:-8000}/healthz` succeeds.
- [x] The README and environment template describe the Docker-only workflow.

**Verification:**

- [x] `docker compose config --quiet` passes.
- [x] `./scripts/check-infrastructure.sh`, `./scripts/smoke-image.sh`, and
  `./scripts/smoke-postgres.sh` pass.

**Dependencies:** Tasks 3 and 5.

**Files likely touched:** `compose.yml`, `.env.example`, `README.md`.

### Checkpoint: Complete framework

- [x] Django tests and the 80% coverage gate pass.
- [x] Ruff formatting and lint checks pass.
- [x] The web container serves `/healthz` and the image health check passes.
- [x] Infrastructure smoke checks pass.
- [x] Each completed slice is committed separately.

## Risks and Mitigations

| Risk | Impact | Mitigation |
| --- | --- | --- |
| Docker runtime cannot import code from `src` | High | Add the import path explicitly in `manage.py` and test inside the image. |
| Database startup race | Medium | Gate `web` on the existing `db` health check. |
| Deployment settings pass locally but fail on Cloud Run | High | Require settings inputs, run `check --deploy`, and bind Gunicorn to `PORT`. |
| Health endpoint leaks deployment details | Medium | Use a constant minimal response and no database query. |

## Scope Exclusions

- No Django apps, models, migrations, admin customization, templates, product
  routes, authentication flows, or browser tests.
- No Google Cloud provisioning, image publication, deployment, or remote
  migrations.
