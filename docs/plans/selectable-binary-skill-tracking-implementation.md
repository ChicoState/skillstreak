# Implementation Plan: Selectable Binary Skill Tracking MVP

## Status

Implemented — verified locally with Django, PostgreSQL, and Chromium browser
tests.

## Dependency Graph

```text
schema.sql design + system-skill catalog
             |
             v
Django tracking models + PostgreSQL migrations
             |
             +---------------------------+
             v                           v
system-skill seed command       internal account registration
             |                           |
             +-------------+-------------+
                           v
      authenticated selection and completion actions
                           |
                           v
           dashboard weekly tracker and browser verification
```

## Task 1: Register internal Django accounts

**Acceptance:** `@csuchico.edu` users can self-register with Django-hashed
passwords; sign-in identifies `request.user` and logout clears the Django
session.

**Verify:** Authentication tests cover registration, sign-in, sign-out, and
invalid credentials.

**Files:** `src/accounts/`, `src/dashboard/`, `.env.example`, `compose.yml`,
tests, and documentation.

## Task 2: Implement the complete tracking schema in Django

**Acceptance:** Django models and migrations faithfully represent every table,
constraint, index, and PostgreSQL exclusion rule in `schema.sql`; model foreign
keys use `settings.AUTH_USER_MODEL`.

**Verify:** Apply migrations to an empty PostgreSQL database; model tests
verify the daily-completion uniqueness and schedule-overlap constraints.

**Files:** `src/tracking/models.py`, `src/tracking/migrations/`, settings,
and model tests.

## Task 3: Seed system skills

**Acceptance:** An idempotent command creates the 109 `SYSTEM` skills in the
catalog; registered users choose their own active skills without duplicate
user-skill rows.

**Verify:** Run the seed command twice and assert unchanged counts.

**Files:** `src/tracking/management/commands/` and command tests.

## Checkpoint: Durable catalog and account ownership

- [x] Migrations work against local PostgreSQL.
- [x] Registered users own separate skill selections.
- [x] All 109 system skills exist once.
- [x] Full tests, coverage, Ruff, and Django checks pass.

## Task 4: Add protected selection and binary-completion actions

**Acceptance:** An authenticated user can activate/deactivate only their own
system skills and toggle only today's completion for their own active
selection. Deactivation preserves history but hides the tracker.

**Verify:** View tests cover POST-only handling, CSRF, idempotence, inactive
selection rejection, and cross-account authorization.

**Files:** `src/tracking/views.py`, URLs, templates, and view tests.

## Task 5: Render the selected-skill dashboard

**Acceptance:** The homepage lists only active selections, offers the complete
skill library with an accessible name search, and shows current UTC weekly
history plus a binary today control for every displayed skill.

**Verify:** Dashboard and browser tests: sign in → search for a skill → select
it → mark today → refresh.

**Files:** `src/dashboard/`, dashboard tests, and browser tests.

## Completion Checkpoint

- [x] Selection and completion data persists per account.
- [x] The dashboard never displays inactive or other-user selections.
- [x] All state changes are accessible, CSRF-protected POST forms.
- [x] Required tests, coverage, image smoke, and browser workflow pass.

## Risks and Mitigations

| Risk | Mitigation |
| --- | --- |
| SQL/Django schema drift | Test constraints and document Django migrations as runtime truth. |
| PostgreSQL extension unavailable | Validate `btree_gist` in the migration before adding exclusion constraints. |
| Default selection duplicates | Use `get_or_create` with model-level unique constraints. |
| Cross-account data exposure | Filter all selection and completion queries by `request.user`. |
| UI scope expands into metrics/schedules | Model them now; do not expose controls until a separate approved slice. |
