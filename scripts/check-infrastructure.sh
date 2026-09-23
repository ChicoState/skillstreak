#!/usr/bin/env sh
set -eu

docker run --rm --volume "$PWD:/workspace:ro" --workdir /workspace python:3.14.7-slim-bookworm \
  python -c 'from pathlib import Path; import tomllib; tomllib.loads(Path("pyproject.toml").read_text())'
docker compose config --quiet
test -f requirements.txt
test -f .github/workflows/pr-checks.yml
test -f .github/workflows/release.yml
