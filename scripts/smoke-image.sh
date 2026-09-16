#!/usr/bin/env sh
set -eu

image=skillstreak-infrastructure-smoke
docker build --target runtime --tag "$image" .
test "$(docker image inspect --format '{{.Config.User}}' "$image")" = "app"
