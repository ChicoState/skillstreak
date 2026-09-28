# SkillStreak

SkillStreak is planned as a public, multi-account Django web application with
PostgreSQL. This repository currently contains its development, quality, Docker,
and delivery foundation only; no Django project, application routes, database
schema, product code, or production deployment exists yet.

## Repository map

| Location | Purpose | Status |
|---|---|---|
| `infrastructure_plan.md` | Approved infrastructure decisions | Current source of truth |
| `requirements.in`, `requirements.txt`, `pyproject.toml` | Python dependencies, resolved lockfile, and tool configuration | Ready |
| `compose.yml`, `Dockerfile`, `.dockerignore` | Local Django/PostgreSQL stack and hardened runtime image | Ready |
| `scripts/` | Infrastructure validation and disposable Docker smoke tests | Ready |
| `tests/application/`, `tests/infrastructure/` | Django framework and infrastructure tests | Ready |
| `docs/specs/`, `docs/plans/` | Reviewed specifications and implementation plans | Bootstrap work documented |
| `.github/workflows/` | Pull-request checks and guarded Cloud Run release workflow | Ready |
| `src/`, `manage.py` | Django project framework and liveness endpoint | Ready; product apps not created |
| `.agents/skills/` | Repository-specific agent guidance | Available |

## Getting Started

1. Install [Git](https://git-scm.com/downloads), [Docker Desktop](https://www.docker.com/products/docker-desktop/), and a current Chrome, Firefox, Safari, or Edge browser. Python is supplied by the development containers; Docker Desktop must be running.
2. Copy the non-secret local template if you need to customize the local database values:

   ```sh
   cp .env.example .env
   ```

   Never commit `.env`. Cloud Run receives real `DATABASE_URL` and
   `DJANGO_SECRET_KEY` values from Google Cloud-managed secrets.
3. Regenerate the dependency lockfile after editing `requirements.in`:

   ```sh
   docker run --rm --volume "$PWD:/workspace" --workdir /workspace python:3.14.7-slim-bookworm \
     sh -c 'python -m pip install "pip-tools>=7.5,<8" && python -m piptools compile --strip-extras --output-file requirements.txt requirements.in'
   ```
4. Start the local Django and PostgreSQL services:

   ```sh
   docker compose up --build
   ```

   The application listens on `http://localhost:8000` by default. Set
   `APP_PORT` in `.env` to choose another host port. Verify its liveness endpoint
   from another terminal:

   ```sh
   curl --fail http://localhost:8000/healthz
   ```

   Run Django commands inside the Docker-only development service:

   ```sh
   docker compose exec web python manage.py check
   docker compose exec web pytest
   docker compose exec web ruff format --check .
   docker compose exec web ruff check .
   ```

5. Validate the static infrastructure configuration:

   ```sh
   ./scripts/check-infrastructure.sh
   ./scripts/smoke-image.sh
   ./scripts/smoke-postgres.sh
   ```

   The PostgreSQL smoke test removes its disposable Compose volume when it finishes.
6. Stop the local stack with `docker compose down`. Remove local database data
   deliberately with `docker compose down --volumes`.

The production image runs Gunicorn and reports a liveness-only `/healthz`
endpoint; it does not query PostgreSQL. Cloud Run must supply
`DJANGO_SETTINGS_MODULE=skillstreak.settings.production`, `DATABASE_URL`,
`DJANGO_SECRET_KEY`, and `ALLOWED_HOSTS` through managed configuration and
secrets. Full Django checks and coverage enforcement now run in pull requests;
migrations and browser workflows remain future product work.

## Quality and CI

`requirements.txt` is the committed pip-tools lockfile. Pull requests verify the
lockfile, Ruff formatting and linting, the infrastructure harness, Gitleaks,
CodeQL, and an image build with a critical-vulnerability scan. Django checks,
coverage (80% branch and line threshold), and browser tests are intentionally
conditional on the future Django application bootstrap.

Release tags (`v*`) target Google Cloud Run through Artifact Registry. Before a
release can run, create the Google Cloud project resources and GitHub production
environment listed in `infrastructure_plan.md`: workload identity provider,
service account, project/region/repository/service/migration-job variables, and
Cloud Run-managed application secrets. The release workflow fails before cloud
authentication while `manage.py` is absent.

## Troubleshooting

- **Docker connection refused or permission denied:** start Docker Desktop, then rerun the command.
- **Port conflicts:** this foundation does not publish PostgreSQL to the host. A future application port will be configurable when its entrypoint exists.
- **Lockfile differs in CI:** regenerate it with the exact container command above and commit both dependency files.
- **Cloud Run release is blocked:** create the Django project first, then configure Google Cloud Workload Identity Federation and the named GitHub production variables/secrets.
