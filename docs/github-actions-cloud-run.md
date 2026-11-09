# GitHub Actions Cloud Run delivery

SkillStreak has separate GitHub Actions delivery paths for development and
production. Pull requests remain validation-only; they never receive Google
Cloud credentials.

## Workflows

- `pr-checks.yml` continues to run pull-request quality, security, container,
  and browser checks.
- `deploy-development.yml` runs only for pushes to `main` and targets the
  `development` GitHub environment.
- `release.yml` runs only for `v*` tags or an explicit `workflow_dispatch` and
  targets the `production` GitHub environment.

Each deployment builds the image once with the exact commit SHA as its tag,
resolves the resulting Artifact Registry digest, scans that immutable digest,
updates the matching migration job's image, waits for migrations to succeed,
and deploys that same digest to Cloud Run. The `gcloud run jobs update` command
changes only `--image`; it does not replace the job's environment variables,
Secret Manager references, Cloud SQL attachment, or service account.

The seed jobs are intentionally not run by deployment workflows. Run them as a
separate, reviewed operation when environment data needs seeding.

## GitHub configuration

Create these repository variables:

| Variable | Value |
| --- | --- |
| `GCP_PROJECT_ID` | `skillstreak-512318` |
| `GCP_REGION` | `us-west1` |
| `ARTIFACT_REGISTRY_REPOSITORY` | `skillstreak-images` |
| `GCP_WORKLOAD_IDENTITY_PROVIDER` | `projects/1006456363037/locations/global/workloadIdentityPools/github-actions/providers/github` |

Create a `development` environment with these environment variables:

| Variable | Value |
| --- | --- |
| `GCP_SERVICE_ACCOUNT` | `skillstreak-dev-deployer@skillstreak-512318.iam.gserviceaccount.com` |
| `CLOUD_RUN_SERVICE` | `skillstreak-dev` |
| `CLOUD_RUN_MIGRATION_JOB` | `skillstreak-dev-migrate` |

Create a `production` environment with the production deployment service account:

| Variable | Value |
| --- | --- |
| `GCP_SERVICE_ACCOUNT` | `skillstreak-prod-deployer@skillstreak-512318.iam.gserviceaccount.com` |
| `CLOUD_RUN_SERVICE` | `skillstreak-prod` |
| `CLOUD_RUN_MIGRATION_JOB` | `skillstreak-prod-migrate` |

Protect the production environment with required reviewers and restrict its
deployment branches/tags to `v*`. Restrict the development environment to
`main`. These rules prevent a manual dispatch from an arbitrary feature branch
from reaching the environment. Environment approvals are an operational guard,
not a replacement for Google Cloud IAM: the workflow identity can still use any
IAM permission granted to the deployment service account.

## Google Cloud IAM hardening

The workflows use separate deployment service accounts for environment
isolation:

- `skillstreak-dev-deployer@skillstreak-512318.iam.gserviceaccount.com`
- `skillstreak-prod-deployer@skillstreak-512318.iam.gserviceaccount.com`

Grant the development account only:

- Artifact Registry writer on `skillstreak-images`.
- Cloud Run developer permissions for `skillstreak-dev` and
  `skillstreak-dev-migrate` (and only the development seed job if it is operated
  separately).
- Service-account user on `skillstreak-dev-runtime`.
- Workload Identity User only for the GitHub repository subject and the
  `development` environment claim.

Grant the production account the corresponding permissions only for
`skillstreak-prod`, `skillstreak-prod-migrate`, and `skillstreak-prod-runtime`.
Remove any obsolete shared account's project-wide `roles/run.developer` after
the replacement bindings are verified. Keep Artifact Registry write permission
scoped to the repository, and avoid granting the GitHub identities Secret
Manager access; Cloud Run runtime service accounts should read runtime secrets.

Configure the Workload Identity Provider attribute condition to require the
repository ID `1363602396` and the intended GitHub environment (`development`
or `production`) for the corresponding service account binding. Do not rely on
the environment name alone: validate the repository identity and branch/tag
claims in the provider and IAM conditions.

## Migration and rollback risks

Migrations run before the new revision receives traffic. A failed migration
stops the workflow before deployment. Schema changes must remain backward
compatible with the currently serving revision until the deployment completes;
expand/contract changes are safer than destructive changes.

The workflow does not automatically reverse migrations. To roll back an
application revision, redeploy a previously verified image digest. If a schema
rollback is required, use a reviewed forward migration or a tested database
restore procedure; do not assume `migrate --fake` or automatic reverse
migrations are safe. The `btree_gist` extension required by the tracking
exclusion constraint must already be permitted for the Cloud SQL migration
user.
