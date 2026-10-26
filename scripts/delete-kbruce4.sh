#!/usr/bin/env bash
set -euo pipefail

readonly TARGET_EMAIL='kbruce4@csuchico.edu'

if [ "${1:-}" != "--confirm" ]; then
  printf 'This permanently deletes %s and records that cascade from it.\n' "$TARGET_EMAIL" >&2
  printf 'Run: %s --confirm\n' "$0" >&2
  exit 64
fi

docker compose exec --no-TTY web python manage.py shell -c "
from accounts.models import User

user = User.objects.filter(email='${TARGET_EMAIL}').first()
if user is None:
    raise SystemExit('No user found for ${TARGET_EMAIL}.')

deleted_count, deleted_by_model = user.delete()
print(f'Deleted {deleted_count} record(s): {deleted_by_model}')
"
