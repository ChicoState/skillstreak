# Spec: SkillStreak Django Source Framework

## Status

Accepted — settings structure, Docker-first development, project name, minimal
source layout, and liveness-only health-check scope are agreed.

## Objective

Create the minimal, Docker-first Django source framework for SkillStreak. It
must establish the project package, safely separate local and production
settings, connect to the existing PostgreSQL Compose service, and expose a
dependency-free `/healthz` endpoint.

It deliberately excludes product apps, models, migrations, authentication
flows, pages, APIs, and business logic.

## Context and Decisions

The repository already provides an approved infrastructure foundation: Python
3.14, Django 5.2 LTS, PostgreSQL, Docker Compose for local development, and a
future Google Cloud Run deployment. It contains no application source.

The following decisions are accepted for this bootstrap:

- The Django project package is named `skillstreak`.
- Local development is Docker-only; host-Python commands are not a supported
  developer workflow.
- Settings use a `base` / `local` / `production` module split.
- The source layout remains minimal until a product feature defines its first
  app boundary.
- A `/healthz` endpoint is included as application plumbing rather than a
  product feature.

Separate settings modules keep Cloud Run security requirements distinct from
local convenience defaults. A single conditional settings module would start
smaller but becomes harder to audit as deployment settings expand.

## Tech Stack

- Python 3.14 and Django 5.2, using the existing locked dependencies.
- PostgreSQL through the existing Compose `db` service.
- Docker Compose as the only supported local developer workflow.
- Django project package: `skillstreak`.

## Commands

After implementation, the supported local application commands will be:

```sh
docker compose up --build
docker compose exec web python manage.py check
docker compose exec web pytest
docker compose exec web ruff format --check .
docker compose exec web ruff check .
curl --fail http://localhost:8000/healthz
```

The existing infrastructure validation remains required:

```sh
./scripts/check-infrastructure.sh
./scripts/smoke-image.sh
./scripts/smoke-postgres.sh
```

## Project Structure

```text
manage.py
src/
  skillstreak/
    __init__.py
    asgi.py
    wsgi.py
    urls.py
    health.py
    settings/
      __init__.py
      base.py
      local.py
      production.py
```

`health.py` remains project plumbing, not a product app. It must not establish
an app-domain convention before a product specification exists.

## Settings Design

- `base.py`: shared Django configuration, installed Django components,
  middleware, templates, and static-file configuration.
- `local.py`: `DEBUG=True`, values supplied through the tracked-safe
  `.env.example` / untracked `.env` convention, and the local Compose
  PostgreSQL connection.
- `production.py`: `DEBUG=False`, production-only HTTPS and secure-cookie
  settings, plus required secret-key, allowed-host, and database configuration.
- `manage.py`, ASGI, and WSGI default to local settings. Cloud Run explicitly
  selects production settings.

## Code Style

Framework code keeps configuration explicit and puts environment access at the
settings boundary rather than scattering it through views:

```python
# settings/production.py
from .base import *

DEBUG = False
SECRET_KEY = required_environment_value("DJANGO_SECRET_KEY")
ALLOWED_HOSTS = comma_separated_environment_value("ALLOWED_HOSTS")
```

Use Python and Django naming conventions, Ruff's existing 100-character line
limit, and direct type annotations for new non-trivial functions.

## Testing Strategy

- Add focused Django tests for `/healthz` and settings selection.
- Preserve the infrastructure harness unchanged except where it must recognize
  the new application framework.
- Run Django checks and the existing pytest coverage gate once `manage.py`
  exists.
- Defer browser testing until the first user-facing feature.

## Boundaries

- **Always:** use Docker for local commands; load secrets and deployment
  configuration from environment variables; keep `/healthz` free of sensitive
  information.
- **Ask first:** add dependencies; add migrations or a database schema; change
  CI or infrastructure-plan decisions; create a product app.
- **Never:** commit `.env` values; add domain behavior; weaken production
  security settings; create a separate frontend or API service.

## Success Criteria

- `docker compose up --build` starts Django and PostgreSQL.
- `/healthz` returns HTTP 200 from the running application.
- Django starts with local settings and connects to Compose PostgreSQL.
- Production settings reject missing required production configuration and
  enable secure deployment defaults.
- The image has a Django command and health check suitable for the planned
  Cloud Run delivery.
- Existing infrastructure checks and the new Django test suite pass.

## Health-Check Scope

`/healthz` is liveness-only: it returns HTTP 200 without querying PostgreSQL.
This avoids transient database availability producing container-health churn.
A database-readiness endpoint may be added later when deployment monitoring
needs it.
