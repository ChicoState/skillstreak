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

   Never commit `.env`; production secrets belong in managed configuration.
3. Start the local services:

   ```sh
   docker compose up --build
   ```

4. In another terminal, prepare the schema and system skill catalog:

   ```sh
   docker compose exec web python manage.py migrate
   docker compose exec web python manage.py seed_system_skills
   ```

   The application listens at `http://localhost:8000` by default. Register an
   internal account, then use the dashboard to select or create skills.

5. Run local checks inside the development container:

   ```sh
   docker compose exec web python manage.py check
   docker compose exec web pytest
   docker compose exec web ruff format --check .
   docker compose exec web ruff check .
   ```

6. Validate infrastructure when needed:

   ```sh
   ./scripts/check-infrastructure.sh
   ./scripts/smoke-image.sh
   ./scripts/smoke-postgres.sh
   ```

   The PostgreSQL smoke test removes its disposable named volume. Stop the
   normal local stack with `docker compose down`.

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
