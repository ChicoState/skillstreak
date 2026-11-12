# Manual Cloud Run deployment

The repository does not automatically deploy the development environment. An
authorized operator can deploy a reviewed image manually with the Google Cloud
CLI. Run these commands from the repository root after authenticating with an
account that has the required environment-scoped permissions.

Set the target values for the environment being operated:

```sh
export PROJECT=skillstreak-512318
export REGION=us-west1
export REPOSITORY=skillstreak-images
export SERVICE=skillstreak-dev
export MIGRATION_JOB=skillstreak-dev-migrate
export IMAGE="$REGION-docker.pkg.dev/$PROJECT/$REPOSITORY/skillstreak:<reviewed-commit-sha>"
```

Build and publish the reviewed image, then update and run the migration job:

```sh
gcloud config set project "$PROJECT"
gcloud auth configure-docker "$REGION-docker.pkg.dev" --quiet
docker build --tag "$IMAGE" .
docker push "$IMAGE"
gcloud run jobs update "$MIGRATION_JOB" --image "$IMAGE" --region "$REGION" --project "$PROJECT"
gcloud run jobs execute "$MIGRATION_JOB" --region "$REGION" --project "$PROJECT" --wait
```

Deploy only after the migration succeeds:

```sh
gcloud run deploy "$SERVICE" \
  --image "$IMAGE" \
  --region "$REGION" \
  --project "$PROJECT"
```

Use the corresponding production service and migration-job names only after
the required production review and approval. The existing production release
workflow remains available for protected `v*` releases.
