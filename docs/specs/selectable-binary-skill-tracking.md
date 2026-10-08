# Spec: Selectable Binary Skill Tracking MVP

## Status

Implemented — local MVP scope.

## Objective

Replace the dashboard's filler skills with a durable, per-account tracker.
Each registered `@csuchico.edu` user can select any skill supplied by
`initial_data.sql`; the dashboard displays only that user's active selections.
Each displayed skill has one binary action: the user did it today, or they did
not.

## Data Contract

`schema.sql` is the approved relational design and `initial_data.sql` is the
approved system-skill catalog. Django models and migrations, not direct SQL
execution, are the runtime implementation source of truth.

All schema entities will be represented in Django:

- `UserPreference`
- `Skill`
- `MetricDefinition`
- `UserSkill`
- `DailyCompletion`
- `UserSkillSchedule`
- `ScheduleWeekday`
- `ScheduleMonthDay`
- `MetricMeasurement`

The MVP user interface uses only `Skill`, `UserSkill`, and `DailyCompletion`.
Metric, schedule, and measurement records are modeled and constrained for
future work but receive no creation or editing controls in this slice.

## Scope

- Register and authenticate internal `@csuchico.edu` users with Django's
  standard login/session facilities.
- Seed all nine system skills from `initial_data.sql` idempotently through a
  Django management command.
- Present a dashboard skill library that lets an authenticated user select or
  deselect any system skill using CSRF-protected POST actions.
- Render only the current user's active selections on the dashboard.
- Toggle today's binary completion for an active selection. A completion row
  means done; its absence means not done.
- Show each selected skill's current UTC Monday-through-Sunday history and
  weekly completed-day count.

## Out of Scope

- Friends, sharing, rankings, messages, notifications, public skills, custom
  skills, password reset, and production provisioning.
- Entering metric values, defining schedules, editing prior completions,
  changing a user's timezone, or a stored streak/leaderboard score.
- Making an inactive selection visible in the dashboard tracker.

## Decisions

- New users begin with no selections and may activate or deactivate any system
  skill, including Touch Grass.
- A deselection sets `UserSkill.is_active=False` rather than deleting history.
- A user may toggle only the authenticated user's active `UserSkill` for the
  current UTC date. Forms contain no owner or date inputs.
- The dashboard's weekly view runs Monday through Sunday and uses Django's
  currently configured UTC application timezone.
- The initial user-facing interaction is binary for every seeded skill,
  regardless of the richer metric and schedule capabilities in the schema.

## Commands

```sh
docker compose up -d db
docker compose run --rm web python manage.py migrate
docker compose run --rm web python manage.py seed_system_skills
docker compose up web
docker compose exec web pytest --cov --cov-branch --cov-fail-under=80 --cov-report=term-missing
docker compose exec web ruff format --check .
docker compose exec web ruff check .
```

## Project Structure

```text
src/
  accounts/                 # Internal user registration and sign-in
  tracking/                 # Schema models, migrations, system-skill seeding
  dashboard/                # Login, selection library, weekly tracker UI
tests/application/          # Model, command, authorization, and view tests
docs/decisions/             # Authentication and data-model decisions
```

## Code Style

Ownership always derives from the authenticated user and selection status is
checked server-side before changing a completion:

```python
user_skill = get_object_or_404(
    UserSkill,
    pk=user_skill_id,
    user=request.user,
    is_active=True,
)
```

## Testing Strategy

- PostgreSQL-backed migration/model tests cover the SQL-equivalent uniqueness,
  check, and exclusion constraints.
- Seeding tests verify all nine system skills are idempotent.
- View tests cover selection, deselection, binary completion toggling,
  unauthenticated requests, CSRF, and cross-account isolation.
- A browser workflow signs in, selects a second skill, marks it complete,
  refreshes, and confirms the other account cannot see that state.

## Boundaries

- Always: use Django migrations, Django password hashing, POST + CSRF for
  state changes, and `request.user` for all ownership checks.
- Ask first: add a system skill, expose metrics or schedules, alter a schema
  constraint, add a third account, or implement friend access.
- Never: run `schema.sql` against an application database, commit credentials,
  accept user/date/selection ownership from a form, or expose inactive skills
  as active dashboard trackers.

## Success Criteria

- All nine seeded skills are available to every registered internal user.
- The dashboard shows exactly the signed-in user's active selections.
- A selected skill's today state and weekly count survive refreshes.
- One account cannot select, deselect, view, or complete another account's
  skills.
