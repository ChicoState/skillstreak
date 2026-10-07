# AGENTS.md

## Status and source of truth

This repository is at the first-account-slice stage. Read
`infrastructure_plan.md` before changing tooling, Docker, CI, dependency, or
delivery decisions. The currently implemented configuration follows that plan:
Python 3.14, Django 5.2 LTS, pip-tools, local PostgreSQL in Compose, and planned
Google Cloud Run delivery through Artifact Registry. The implemented product
slice combines internal `@csuchico.edu` account registration with a
PostgreSQL-backed selected-skill tracker; production account behavior does not
exist yet.

## Repository map

- `infrastructure_plan.md`: approved infrastructure plan.
- `requirements.in`, `requirements.txt`, `requirements.runtime.in`,
  `requirements.runtime.txt`, `pyproject.toml`, `.python-version`: Python
  toolchain and development/runtime lockfiles.
- `compose.yml`, `Dockerfile`, `.dockerignore`, `.env.example`: Docker infrastructure and safe local configuration template.
- `scripts/`: infrastructure validation, container-image, and PostgreSQL smoke tests.
- `tests/infrastructure/`: configuration harness tests only.
- `.github/workflows/`: `pr-checks.yml` and guarded `release.yml`.
- `.agents/skills/`: repository-provided skills.
- `src/accounts/`: email-only internal team accounts and first user migration.
- `src/dashboard/`: authenticated selected-skill dashboard.
- `src/tracking/`: tracking schema, migrations, seeding, selection, and binary
  daily-completion behavior.
- `docs/specs/internal-team-accounts.md`: approved account scope.
- `docs/decisions/002-internal-email-accounts.md`: account-authentication
  rationale.
- `docs/specs/selectable-binary-skill-tracking.md`: selected-skill scope.
- Browser tests and production account flows: **not created yet**.

## Required reading and skill routing

Read this file, `infrastructure_plan.md`, and any applicable local skill before
making a change. Use `infra-planner` to revise infrastructure decisions and
`infra-builder` for infrastructure-only implementation. Use
`spec-driven-development` or `planning-and-task-breakdown` before significant
product work; `frontend-ui-engineering` for user-facing UI; and
`test-driven-development` plus `test-in-browser` / `browser-testing-with-devtools`
for application behavior and browser verification. Use
`security-and-hardening`, `documentation-and-adrs`, `ci-cd-and-automation`,
`code-review-and-quality`, and `git-workflow-and-versioning` when their scopes
apply.

## Boundaries

- During infrastructure work, do not create unrelated Django apps, pages,
  routes, models, domain schemas, authentication flows, business logic, product
  fixtures, or production data.
- Do not change a plan decision without updating `infrastructure_plan.md` through
  the planning workflow.
- Never commit secrets, `.env` files, credentials, generated reports, local
  volumes, or build artifacts.
- Do not provision Google Cloud resources, publish images, deploy, or run remote
  migrations from this repository setup task.

## Verification and lifecycle

Run `./scripts/check-infrastructure.sh`, `./scripts/smoke-image.sh`, and
`./scripts/smoke-postgres.sh` after infrastructure changes. These correspond to
the currently meaningful local PR checks; GitHub Actions additionally runs
Gitleaks, CodeQL, and Trivy. `smoke-postgres.sh` cleans up containers and volumes.
For persistent local database work, use `docker compose up -d db`, then clean up
with `docker compose down` (or `docker compose down --volumes` only when you
intend to discard local data).

## Change checklist

1. Keep the change within the active plan and boundary.
2. Update the lockfile after dependency input changes.
3. Run the applicable verification commands and `git diff --check`.
4. Inspect the final diff for secrets and generated files.
5. Update this file and `README.md` whenever paths, commands, prerequisites, or
   developer workflow change.
