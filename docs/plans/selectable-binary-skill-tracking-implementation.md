# Implementation Plan: Selectable Binary Skill Tracking MVP

## Status

Implemented — verified locally with Django tests and PostgreSQL.

## Dependency Graph

```text
schema.sql + initial_data.sql design
             |
             v
Django tracking models + PostgreSQL migrations
             |
             +---------------------------+
             v                           v
system-skill seed command       two-user provision command
             |                           |
             +-------------+-------------+
                           v
      authenticated selection and completion actions
                           |
                           v
           dashboard weekly tracker and browser verification
```

## Task 1: Replace temporary demo auth with two Django accounts

**Acceptance:** Two `.env`-configured demo users are created idempotently with
Django-hashed passwords; sign-in identifies `request.user` and logout clears
the Django session.

**Verify:** Authentication tests cover both accounts and invalid credentials.

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

## Task 3: Seed system skills and default Touch Grass selection

**Acceptance:** An idempotent command creates all nine `SYSTEM` skills from
`initial_data.sql`; provisioning makes only Touch Grass active for each demo
user without duplicate user-skill rows.

**Verify:** Run seed/provision commands twice and assert unchanged counts and
default selections.

**Files:** `src/tracking/management/commands/`, `src/accounts/management/`,
and command tests.

## Checkpoint: Durable catalog and account ownership

- [ ] Migrations work against local PostgreSQL.
- [ ] Both demo users own separate Touch Grass selections.
- [ ] All nine system skills exist once.
- [ ] Full tests, coverage, Ruff, and Django checks pass.

## Task 4: Add protected selection and binary-completion actions

**Acceptance:** An authenticated user can activate/deactivate only their own
system skills and toggle only today's completion for their own active
selection. Deactivation preserves history but hides the tracker.

**Verify:** View tests cover POST-only handling, CSRF, idempotence, inactive
selection rejection, and cross-account authorization.

**Files:** `src/tracking/views.py`, URLs, templates, and view tests.

## Task 5: Render the selected-skill dashboard

**Acceptance:** The homepage lists only active selections, offers the complete
skill library, and shows current UTC weekly history plus a binary today control
for every displayed skill.

**Verify:** Dashboard tests and browser path: sign in → select a skill → mark
today → refresh → log out → sign in as the other user.

**Files:** `src/dashboard/`, dashboard tests, and browser tests.

## Completion Checkpoint

- [ ] Selection and completion data persists per account.
- [ ] The dashboard never displays inactive or other-user selections.
- [ ] All state changes are accessible, CSRF-protected POST forms.
- [ ] Required tests, coverage, image smoke, and browser workflow pass.

## Risks and Mitigations

| Risk | Mitigation |
| --- | --- |
| SQL/Django schema drift | Test constraints and document Django migrations as runtime truth. |
| PostgreSQL extension unavailable | Validate `btree_gist` in the migration before adding exclusion constraints. |
| Default selection duplicates | Use `get_or_create` with model-level unique constraints. |
| Cross-account data exposure | Filter all selection and completion queries by `request.user`. |
| UI scope expands into metrics/schedules | Model them now; do not expose controls until a separate approved slice. |
