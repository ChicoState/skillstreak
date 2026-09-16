#!/usr/bin/env sh
set -eu

cleanup() {
  docker compose down --volumes --remove-orphans
}
trap cleanup EXIT INT TERM

docker compose up --detach db
container_id=$(docker compose ps --quiet db)
attempt=0
until [ "$(docker inspect --format '{{.State.Health.Status}}' "$container_id")" = "healthy" ]; do
  attempt=$((attempt + 1))
  if [ "$attempt" -ge 30 ]; then
    echo "PostgreSQL did not become healthy within 60 seconds." >&2
    exit 1
  fi
  sleep 2
done
docker compose exec --no-TTY db psql --username "${POSTGRES_USER:-skillstreak}" --dbname "${POSTGRES_DB:-skillstreak}" --command 'SELECT 1;'
