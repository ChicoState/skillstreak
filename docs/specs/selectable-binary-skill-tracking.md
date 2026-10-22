# Spec: Selectable Binary Skill Tracking MVP

## Status

Implemented — local MVP scope.

## Objective

Replace the dashboard's filler skills with a durable, per-account tracker.
Each registered `@csuchico.edu` user can select any skill in the system
catalog; Dashboard lists all active selections, while an authorized selected
skill opens one detailed tracker at a time. Each displayed skill has one binary
action: the user did it today, or they did not.

## Data Contract

`schema.sql` is the approved relational design. Django models, migrations, and
the system-skill management command, not direct SQL execution, are the runtime
implementation source of truth.

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
- `Tag`
- `TagAlias`
- `SkillTag`

The MVP user interface uses `Skill`, `Tag`, `TagAlias`, `SkillTag`, `UserSkill`,
and `DailyCompletion`. Metric, schedule, and measurement records are modeled
and constrained for future work but receive no creation or editing controls in
this slice.

## Scope

- Register and authenticate internal `@csuchico.edu` users with Django's
  standard login/session facilities.
- Seed the 109-skill system catalog idempotently through a Django management
  command. The catalog retains its original nine skills and adds 100 distinct,
  general-audience daily skills.
- Present a compact, unified Skill library tab containing system skills and the
  signed-in member's private skills. Private entries retain a `My skill` badge.
  Let an authenticated user select or deselect an available skill using
  CSRF-protected POST actions and narrow the collection by name or description
  with an accessible GET search form. JavaScript enhances the form into live,
  no-reload filtering while preserving the GET behavior for users without
  JavaScript.
- Give each system skill a short description and one to three curated tags.
  Search matches skill text, tag names, and curated aliases; an optional tag
  filter combines with text search.
- Make Dashboard the post-login landing page. It lists all of the current
  user's active selections as compact cards and retains a sidebar subsection
  for quick selection.
- Render a detailed selected-skill tracker only when an active, owned
  `UserSkill` ID is present in the URL. Detail includes supported frequency,
  goal deadline, current-week check-ins, and current-month completion history.
- Treat Dashboard and Skill library as validated sidebar views. Dashboard is
  the default; the optional `view=library` URL state renders the library without
  loading a tracker card.
- Toggle today's binary completion for an active selection. A completion row
  means done; its absence means not done.
- Show each selected skill's current UTC Monday-through-Sunday history and
  weekly completed-day count.

## Out of Scope

- Friends, sharing, rankings, messages, notifications, public custom skills,
  editing/deleting custom skills, password reset, and production provisioning.
- Entering metric values, defining schedules, editing prior completions,
  changing a user's timezone, or a stored streak/leaderboard score.
- Making an inactive selection visible in the dashboard tracker.

## Decisions

- New users begin with Touch Grass selected and may activate or deactivate any
  system skill, including Touch Grass.
- A deselection sets `UserSkill.is_active=False` rather than deleting history.
- A user may toggle only the authenticated user's active `UserSkill` for the
  current UTC date. Forms contain no owner or date inputs.
- The dashboard's weekly view runs Monday through Sunday and uses Django's
  currently configured UTC application timezone.
- The initial user-facing interaction is binary for every seeded skill,
  regardless of the richer metric and schedule capabilities in the schema.
- A user-created skill is `PRIVATE`, owned by its creator, and immediately
  selected for that user. Its goal is daily, an any-N-days weekly goal, or an
  any-N-days calendar-month goal. The completion action remains binary; the
  dashboard derives progress for the current goal period.
- A private skill appears only in its creator's unified library and search
  results. Removing it from the tracker preserves its history and allows the
  creator to re-add it.
- The enhanced library renders only system skills and the current member's
  private skills in one alphabetical collection. Because it has its own tab,
  all authorized skills render directly; no expansion controls hide entries.
- The selected tracker is represented by an optional `skill` URL parameter
  containing a `UserSkill` ID. The dashboard accepts it only when the record is
  active and owned by the signed-in user; missing or invalid values render the
  Dashboard landing. Adding or reactivating a skill opens that tracker, while a
  completion action from its detail keeps its tracker selected. Every Dashboard
  landing card also has a compact completion action that returns to the landing.
- Adding or reactivating a skill opens its Dashboard tracker. Removing a skill
  from the library returns to that tab while retaining valid library filters.
- Live search reads rendered text rather than constructing HTML from a query or
  user-created skill content. It updates the URL with `history.replaceState`,
  announces its result count, and keeps the query in selection forms so an
  add/remove action returns to the same search state.
- Tags belong to a fixed taxonomy. A private skill receives one best-matching
  existing tag based on deterministic name/description keyword scoring, with
  `General` as the fallback; members cannot create tags or aliases.

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
- Seeding tests verify the 109-skill catalog is idempotent, contains unique
  slugs, and retains the original skills.
- View tests cover system and owner-private selection, deselection, binary
  completion toggling, selected-tracker authorization/fallback, unauthenticated
  requests, CSRF, search, unified compact library behavior, tag aliases/filters,
  and cross-account isolation.
- Browser workflows verify that search filters as text is entered, every
  authorized library skill is visible without expansion, Dashboard opens the
  all-skills landing, a selected detail can return to that landing, and
  completion remains on the selected tracker after refresh or can be toggled
  directly from its landing card.

## Boundaries

- Always: use Django migrations, Django password hashing, POST + CSRF for
  state changes, and `request.user` for all ownership checks.
- Ask first: expose metrics or schedules, alter a schema constraint, add a
  third account, or implement friend access.
- Never: run `schema.sql` against an application database, commit credentials,
  accept user/date/selection ownership from a form, or expose inactive skills
  as active dashboard trackers.

## Success Criteria

- All 109 seeded skills are available to every registered internal user.
- Dashboard lists exactly the signed-in user's active selections, and its main
  detail appears only for the selected one.
- A selected skill's today state and weekly count survive refreshes.
- One account cannot select, deselect, view, or complete another account's
  skills.
