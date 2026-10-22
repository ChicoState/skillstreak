#!/usr/bin/env sh
set -eu

image=skillstreak-infrastructure-smoke
container_id=

cleanup() {
  if [ -n "$container_id" ]; then
    docker rm --force "$container_id" >/dev/null 2>&1 || true
  fi
}
trap cleanup EXIT INT TERM

docker build --target runtime --tag "$image" .
test "$(docker image inspect --format '{{.Config.User}}' "$image")" = "app"
container_id=$(docker run --detach "$image")

attempt=0
until [ "$(docker inspect --format '{{.State.Health.Status}}' "$container_id")" = "healthy" ]; do
  attempt=$((attempt + 1))
  if [ "$attempt" -ge 15 ]; then
    echo "Application image did not become healthy within 30 seconds." >&2
    exit 1
  fi
  sleep 2
done
