# SkillStreak

SkillStreak is a multi-account Django web application with PostgreSQL. The
current local product slice provides internal `@csuchico.edu` account
registration/sign-in, private scheduled skills, selected system skills,
completion tracking, reminders, and dashboard progression.

## Repository map

| Location | Purpose | Status |
|---|---|---|
| `infrastructure_plan.md` | Approved infrastructure decisions | Current source of truth |
| `requirements.in`, `requirements.txt`, `pyproject.toml` | Python dependencies, lockfile, and tool configuration | Ready |
| `compose.yml`, `Dockerfile`, `.dockerignore` | Local Django/PostgreSQL stack and hardened runtime image | Ready |
| `scripts/` | Infrastructure validation and disposable Docker smoke tests | Ready |
| `tests/application/`, `tests/browser/`, `tests/infrastructure/` | Django, Chromium browser, and infrastructure tests | Ready |
| `docs/specs/`, `docs/plans/`, `docs/decisions/` | Reviewed product scope and decisions | Current |
| `src/skills/` | Account-owned scheduled skills and XP/level progression | Implemented |
| `src/tracking/` | Selected skills, schedules, reminders, and completion tracking | Implemented |
| `src/profiles/` | Profile and reminder preferences | Implemented |

## Getting started

1. Install [Git](https://git-scm.com/downloads), [Docker Desktop](https://www.docker.com/products/docker-desktop/), and a current Chrome, Firefox, Safari, or Edge browser.
2. Optionally copy the non-secret local template:

   ```sh
   cp .env.example .env
   ```

   Never commit `.env`. Cloud Run receives `DJANGO_SECRET_KEY`, explicit
   `ALLOWED_HOSTS`, and (for Cloud SQL socket connections) the four
   `CLOUD_SQL_*` values from Google Cloud-managed secrets/configuration.
3. Regenerate the dependency lockfiles after editing `requirements.in` or the
   production-only `requirements.runtime.in`:

   ```sh
   docker run --rm --volume "$PWD:/workspace" --workdir /workspace python:3.14.7-slim-bookworm \
     sh -c 'python -m pip install "pip-tools>=7.5,<8" && python -m piptools compile --strip-extras --output-file requirements.txt requirements.in && python -m piptools compile --strip-extras --output-file requirements.runtime.txt requirements.runtime.in'
   ```
4. Start the local Django and PostgreSQL services:
   ```sh
   docker compose up --build
   ```

5. In another terminal, prepare the schema and system skill catalog:

   ```sh
   docker compose exec web python manage.py migrate
   docker compose exec web python manage.py seed_system_skills
   ```

   The application listens at `http://localhost:8000` by default. Register an
   internal account, then use the dashboard to select or create skills.

6. Run local checks inside the development container:

   ```sh
   docker compose exec web python manage.py check
   docker compose exec web pytest
   docker compose exec web ruff format --check .
   docker compose exec web ruff check .
   ```

7. Validate infrastructure when needed:

   ```sh
   ./scripts/check-infrastructure.sh
   ./scripts/smoke-image.sh
   ./scripts/smoke-postgres.sh
   ```

   The PostgreSQL smoke test stops the Compose stack and removes its named
   PostgreSQL volume when it finishes. Run it only when local database data is
   disposable.
8. Stop the local stack with `docker compose down`. Remove local database data
   deliberately with `docker compose down --volumes`.

The production image runs Gunicorn, collects static files at image build time,
serves them through WhiteNoise, and reports a liveness-only `/healthz` endpoint;
it does not query PostgreSQL. Cloud Run must supply
`DJANGO_SETTINGS_MODULE=skillstreak.settings.production`, `DJANGO_SECRET_KEY`,
and explicit `ALLOWED_HOSTS`. Production database configuration can either use
`DATABASE_URL` (including a PostgreSQL `?host=/cloudsql/…` Unix-socket query
parameter) or `CLOUD_SQL_CONNECTION_NAME`, `CLOUD_SQL_DATABASE`,
`CLOUD_SQL_USER`, and `CLOUD_SQL_PASSWORD`. `CSRF_TRUSTED_ORIGINS` is optional
and defaults to `https://` origins derived from `ALLOWED_HOSTS`; set it when the
accepted browser origins differ from the hostnames.

The existing tracking migration creates the PostgreSQL `btree_gist` extension
before adding its exclusion constraint. The Cloud SQL runtime user must have
permission to create that extension during the controlled release migration;
this repository does not run migrations against Cloud SQL.
## Quality and CI

Pull requests verify the lockfile, Ruff, infrastructure configuration,
Gitleaks, CodeQL, Trivy, Django checks, the 80% coverage gate, and focused
Chromium browser workflows. The production image targets Google Cloud Run
through Artifact Registry; deployment requires the protected configuration
listed in `infrastructure_plan.md`.

## Troubleshooting

- **Docker connection refused:** start Docker Desktop and rerun the command.
- **Port conflicts:** set `APP_PORT` in `.env`.
- **Lockfile differs in CI:** regenerate the lockfiles with the documented
  pip-tools container command in the project history.
