# Spec: Gym Daily Completion MVP

## Status

Superseded by `selectable-binary-skill-tracking.md`.

## Objective

Let each of two local demo accounts mark whether they went to the gym today and
see their own Monday-through-Sunday completion history on the homepage. This is
the smallest durable implementation of the user's consistency goal.

User story: *As a college student, I want a tool to allow me to track my
consistency in the gym throughout the week and compete with my friends who also
have the same goal because I want to exercise consistently.*

The MVP delivers private, per-account history. It deliberately establishes the
ownership boundary needed for future friend comparison but does not implement
friends, shared views, rankings, invitations, or notifications.

## Scope

- Replace the single fixed demo sign-in with two local Django users whose
  credentials are supplied through untracked environment variables.
- Add an idempotent local command that creates or updates those two users with
  Django-managed password hashes.
- Add a `GymCompletion` model containing the authenticated user, completion
  date, and creation timestamp, with a database uniqueness constraint on
  `(user, completed_on)`.
- Show the signed-in user's current Monday-through-Sunday history and completed
  day count on the homepage.
- Provide one CSRF-protected POST action that toggles today's completion.
- Permit the signed-in user to view and change only their own record.

## Out of Scope

- Account registration, password reset, arbitrary accounts, and production
  demo-account provisioning.
- Other skills, quantities, schedules, historical backfill, editing previous
  days, friends, leaderboards, or notifications.
- A stored streak counter. Future streak and leaderboard values derive from
  completion rows.

## Decisions

- Use Django's built-in user model and `authenticate()` / `login()` rather
  than comparing plaintext demo credentials in a view.
- Configure exactly two local accounts through
  `DEMO_ACCOUNT_1_EMAIL` / `DEMO_ACCOUNT_1_PASSWORD` and
  `DEMO_ACCOUNT_2_EMAIL` / `DEMO_ACCOUNT_2_PASSWORD` in `.env`.
- Use each configured email as the Django username for this local MVP.
- Treat a completion as a date, not a boolean column: the presence of the row
  means the user went to the gym. Removing the row marks today incomplete.
- Define a week as Monday through Sunday. “Today” follows Django's currently
  configured UTC application timezone; per-user timezones are deferred.

## Commands

```sh
docker compose up -d db
docker compose run --rm web python manage.py migrate
docker compose run --rm web python manage.py provision_demo_users
docker compose up web
docker compose exec web pytest --cov --cov-branch --cov-fail-under=80 --cov-report=term-missing
docker compose exec web ruff format --check .
docker compose exec web ruff check .
```

## Project Structure

```text
src/
  accounts/                 # Local demo-user provisioning command
  gym/                      # GymCompletion model and today-toggle view
  dashboard/                # Homepage presentation of authenticated history
tests/application/          # Model, authentication, authorization, and view tests
docs/decisions/             # Authentication-design history
```

## Code Style

Use the authenticated user as the sole ownership source; never accept a user
identifier from a form:

```python
GymCompletion.objects.get_or_create(
    user=request.user,
    completed_on=timezone.localdate(),
)
```

## Testing Strategy

- Model test: a user cannot have two GymCompletion records on one date.
- Authentication tests: each configured demo account can sign in; invalid
  credentials cannot.
- View tests: an unauthenticated request is redirected; a valid POST creates,
  then removes, only the current user's completion; a user cannot see another
  user's history.
- Browser test: sign in, mark today, refresh, verify the state persists, then
  log out.

## Boundaries

- Always: hash passwords through Django, protect state changes with POST and
  CSRF, derive ownership from `request.user`, and use migrations for schema
  changes.
- Ask first: add a third account, change the week/timezone definition, add
  friend access, or change the database schema beyond `GymCompletion`.
- Never: commit account credentials, expose another user's completions, or
  trust a submitted user ID or completion date.

## Success Criteria

- The two environment-configured demo accounts can sign in independently.
- Each account sees only its own Gym history.
- Checking today's Gym control persists one row; unchecking removes it.
- Refreshing preserves the correct state and weekly count for the same user.
- One account's actions do not change the other account's homepage.
