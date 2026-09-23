# Infrastructure Plan

> Planning only. This document describes future infrastructure work. No installations, configuration changes, containers, workflows, deployments, or other implementation files were created by the infrastructure-planning process.

## 1. Project and User Experience

- **Application:** Public-facing, multi-account web application (name and exact domain to be confirmed).
- **Primary users:** Members of the public with individual accounts.
- **Primary user task:** Access shared or collaborative application data through a browser.
- **Selected platform:** Responsive browser-based web application.
- **User-experience rationale:** Immediate access from a link best meets the selected public-facing experience while supporting desktop and mobile browsers.
- **Required operating systems, browsers, or devices:** Current Chrome, Firefox, Safari, and Edge on desktop and mobile.
- **Offline or native-device requirements:** None confirmed; an internet connection is required.

## 2. Connectivity and Application Shape

- **Connectivity model:** Multi-user web-enabled.
- **Accounts and authentication:** Django's built-in authentication, extended only as required by product requirements; password handling remains Django-managed.
- **Backend required:** Yes; one Django application serves the web experience and application logic.
- **Cross-device persistence:** Yes, through hosted PostgreSQL associated with user accounts.
- **Interaction between accounts:** Shared or collaborative data is supported; authorization rules must be defined per product feature before implementation.
- **Primary application components:** Django web application, PostgreSQL database, and a reverse-proxy/container-host boundary in production.

## 3. Selected Technology Stack

| Area | Selected technology | Purpose | Version policy |
|---|---|---|---|
| Primary language | Python | Application code and server-rendered web behavior | Python 3.14; pin the current supported 3.14 patch release in the lockfile/image update cycle |
| Application framework | Django | Web UI, authentication, ORM, admin, and migrations | Django 5.2 LTS; the verified current package-index patch is 5.2.17, pinned in the lockfile |
| Runtime or SDK | CPython | Runs Django and tooling | CPython 3.14 |
| Package manager | pip with pip-tools (`pip-compile` / `pip-sync`) | Reproducible Python dependencies | Pin direct dependencies in `requirements.in` and resolved dependencies in committed `requirements.txt` |
| Build or packaging tool | Docker multi-stage build | Produce a portable production image | Pinned base-image digests or supported tags |
| Backend framework | Django | Single deployable application; no separate API is planned initially | Same as application framework |

## 4. Storage and Persistence

- **Storage model:** Hosted relational storage.
- **Primary data store:** Managed PostgreSQL in production.
- **User files or object storage:** Not planned; no user uploads were selected.
- **Local-development storage:** PostgreSQL service in Docker Compose with a named volume.
- **Production hosting model:** Google Cloud Run for the Django container and a compatible managed PostgreSQL provider; Cloud Run must receive the database connection string and Django settings through its managed secret/configuration mechanisms.
- **Schema and migration approach:** Django migrations, reviewed with application changes and run once during a controlled release deployment.
- **Backup, export, or recovery approach:** Enable provider-managed point-in-time recovery or scheduled backups; document restoration testing before production launch.
- **Secrets and connection-string approach:** Database connection strings and Django secret keys belong in the host's secret manager and GitHub Actions secrets, never in images or source control.
- **Reason this storage fits the access pattern:** PostgreSQL provides durable, transactional shared data for multiple authenticated users.

## 5. Testing Tools

| Test layer | Tool or library | Planned scope | Planned execution point |
|---|---|---|---|
| Unit | pytest and pytest-django | Models, forms, permissions, and business rules | Local and pull requests |
| Integration | pytest-django with PostgreSQL | Views, authentication, ORM queries, and migrations | Local and pull requests |
| End-to-end or UI | Playwright | Critical public, sign-in, and collaboration workflows | Pull requests when practical; release validation |

## 6. Test Analysis

| Capability | Tool | Planned policy |
|---|---|---|
| Coverage | coverage.py with pytest-cov | Collect line and branch coverage for Python tests |
| Coverage threshold or regression rule | pytest-cov configuration | Enforce a modest initial 80% project coverage floor on pull requests; increase only with deliberate agreement |
| Reporting | Coverage XML and terminal report | Upload XML as a pull-request artifact; retain it for failed checks |

## 7. Static Analysis and Security

| Check | Tool | Planned enforcement |
|---|---|---|
| Formatting | Ruff formatter | Verify on every pull request; block merging on differences |
| Linting | Ruff | Run on every pull request; block merging on findings |
| Type checking or compiler warnings | Django system checks | Run deployment-oriented Django checks in pull requests and releases |
| Dependency vulnerability scanning | Dependabot | Open dependency update and security-alert pull requests; review before merge |
| Secret scanning | Gitleaks | Scan pull requests and the release branch; block on findings |
| Static security analysis | GitHub CodeQL for Python | Analyze pull requests and scheduled default-branch scans; block high-confidence actionable findings |
| Container scanning | Trivy | Scan the production image before publication; block critical findings |

## 8. Development Technologies Requiring Manual Installation

These are developer-workstation prerequisites that will not be supplied by the planned Docker environment.

| Technology | Why it is needed | Required on which machines | Version policy | Planned installation or verification method | Why Docker does not provide it |
|---|---|---|---|---|---|
| Git | Source control and GitHub workflow | All developer workstations | Current supported release | Future onboarding verification | Host integration and credentials remain local |
| Docker Desktop or Docker Engine with Compose | Run local Django and PostgreSQL containers | All developer workstations | Current supported release | Future onboarding verification | Docker must run on the host |
| Web browser | Manual responsive and accessibility checks | All developer workstations | Current stable browser | Future onboarding verification | Browser UI is a host application |

### Host tools intentionally not required

- **Not required because Docker supplies them:** Python, pip, Django, PostgreSQL, test tools, Ruff, and Gitleaks.
- **Not required for this platform:** Xcode, Android Studio, Rust, desktop packaging SDKs, and mobile signing tools.

## 9. Docker Plan

- **Planned Docker role:** Development and production.
- **Future files that would be created during implementation:** `pyproject.toml`, `requirements.in`, `requirements.txt`, `Dockerfile`, `compose.yml`, `.dockerignore`, and an example environment-variable template.
- **Planned images and services:** Django application image and PostgreSQL service locally; the production database remains managed rather than containerized.
- **Development container behavior:** Compose runs the application and PostgreSQL together with application source bind-mounted for iteration.
- **Ports:** Bind the Django development service to a configurable local port; expose PostgreSQL only to the Compose network unless direct host access is needed.
- **Bind mounts and named volumes:** Source bind mount for development; named PostgreSQL volume for local persistence; no production source mount.
- **Environment-variable and secret handling:** Local uncommitted environment file; production secrets injected by the managed host; never bake secrets into images.
- **Local database or service containers:** PostgreSQL only.
- **Production image or non-container release path:** Publish a hardened Django container image to Google Artifact Registry and deploy it to Google Cloud Run.
- **Build stages and hardening:** Multi-stage build, minimal runtime image, non-root user, `.dockerignore`, health endpoint/check, pinned bases, and no embedded secrets.

## 10. GitHub Actions Plan

### A. Automated pull-request checks

- **Future workflow file:** `.github/workflows/pr-checks.yml`; install dependencies with `pip-sync requirements.txt`.
- **Trigger:** `pull_request` as the primary trigger.
- **Runner or matrix:** Ubuntu runner; one supported Python version initially, with a future matrix only if multiple versions are supported.
- **Permissions:** Read-only repository contents; grant only per-job write permissions where an uploaded report requires them.
- **Planned jobs in order:**
  1. Checkout, set up Python, restore pip cache, and install from the future lockfile.
  2. Verify Ruff formatting and run Ruff linting.
  3. Start a PostgreSQL service container, run Django checks, migrations validation, pytest-django tests, and coverage enforcement.
  4. Run Gitleaks and CodeQL analysis.
  5. Build the container image without publishing, scan it with Trivy, and run focused Playwright browser workflows where practical.
- **Service containers:** PostgreSQL for Django integration tests.
- **Caching:** Cache pip downloads keyed by Python version and the future lockfile hash; cache Playwright browsers if end-to-end checks run.
- **Coverage and analysis reporting:** Upload coverage XML and retain CodeQL results in GitHub Security.
- **Failure artifacts:** Coverage XML, Playwright trace/screenshots, Django test output, and container-scan results.
- **Checks that should block merging:** Formatting, linting, Django checks, tests, 80% coverage threshold, critical container findings, confirmed secrets, and actionable security findings.
- **Proposed branch-protection settings:** Require the named checks, require an approving review, require the branch to be current, and restrict direct pushes to the default branch.

### B. New-release deployment

- **Future workflow file:** `.github/workflows/release.yml`
- **Release trigger:** Protected `v*` tag, with `workflow_dispatch` for a controlled redeploy.
- **Release destination:** Google Cloud Run, with images published to Google Artifact Registry.
- **Runner or matrix:** Ubuntu runner for image build, scanning, registry publication, and provider deployment.
- **Planned jobs in order:**
  1. Checkout the tagged revision and repeat essential validation, including Django checks and tests.
  2. Build, tag, scan, and publish the signed-by-digest container image to the selected registry.
  3. Request protected-environment approval, apply Django migrations as a one-off release step, and deploy the image.
  4. Run an authenticated or public smoke check against the deployed health endpoint and publish concise release notes.
- **Build artifacts:** Immutable image digest, scan report, and release notes.
- **Signing, notarization, or store requirements:** No desktop or mobile signing; use registry authentication and, if supported by the chosen provider, image provenance/signing.
- **Database migration step:** Run `python manage.py migrate` once, from the release job or provider release mechanism, before serving the new version; ensure migration compatibility is reviewed.
- **Environment approval:** GitHub Environment protection for production deployment.
- **Post-deployment verification:** Health endpoint and one critical browser or HTTP smoke workflow.
- **Failed-release or rollback approach:** Redeploy the previous known-good image digest; do not automatically reverse migrations unless a documented migration-specific rollback is safe.

### GitHub configuration required later

| Name | Type | Purpose |
|---|---|---|
| `PRODUCTION` | GitHub environment | Protection rules and production-scoped deployment secrets |
| `GCP_WORKLOAD_IDENTITY_PROVIDER` | Variable | Google Cloud Workload Identity Federation provider resource name used by GitHub Actions |
| `GCP_SERVICE_ACCOUNT` | Variable | Least-privilege Google Cloud service-account email used by GitHub Actions through workload identity federation |
| `GCP_PROJECT_ID` | Variable | Google Cloud project that contains Artifact Registry and Cloud Run resources |
| `GCP_REGION` | Variable | Google Cloud region for Artifact Registry and Cloud Run |
| `ARTIFACT_REGISTRY_REPOSITORY` | Variable | Artifact Registry Docker repository name |
| `CLOUD_RUN_SERVICE` | Variable | Cloud Run service name to deploy |
| `CLOUD_RUN_MIGRATION_JOB` | Variable | Cloud Run Job name that runs the release migration exactly once |
| `DATABASE_URL` | Secret | Production PostgreSQL connection string for migration and application runtime |
| `DJANGO_SECRET_KEY` | Secret | Django cryptographic signing secret |
| `ALLOWED_HOSTS` | Variable | Public hostnames accepted by Django |
| Managed container-host account | Provider account | Run the deployed container and inject runtime secrets |
| Managed PostgreSQL account/service | Provider account | Host production relational data and backups |

## 11. Planned Repository Artifacts - Not Created by This Skill

- [ ] Application manifest or project file: Python tool configuration plus `requirements.in`.
- [ ] Lockfile: Resolved, reproducible `requirements.txt` generated by pip-tools.
- [ ] Test configuration: pytest, coverage, and Playwright configuration.
- [ ] Static-analysis configuration: Ruff, Gitleaks, and CodeQL configuration as applicable.
- [ ] Docker or Compose files: `Dockerfile`, `compose.yml`, and `.dockerignore`.
- [ ] `.github/workflows/pr-checks.yml`: Pull-request verification workflow.
- [ ] `.github/workflows/release.yml`: Tag-triggered production release workflow.
- [ ] Deployment or store configuration: Selected managed-container-host configuration.

## 12. Assumptions and Open Items

- **Assumptions:** The application needs conventional account authentication, no file uploads, and no offline-first behavior; one Django deployable is sufficient.
- **Decisions still requiring an external account, credential, certificate, or organizational approval:** Create/select the Google Cloud project, Artifact Registry repository, Cloud Run service, managed PostgreSQL provider, public domain, production owner, and workload-identity/service-account permissions.
- **Items to confirm before implementation begins:** Exact authorization rules for collaboration, legal/privacy needs for public accounts, retention period for backups, and the initial test coverage baseline after the first test suite exists.
