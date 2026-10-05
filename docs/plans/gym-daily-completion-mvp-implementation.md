# Implementation Plan: Gym Daily Completion MVP

## Status

Superseded by `selectable-binary-skill-tracking-implementation.md`.

## Dependency Graph

```text
two environment credentials
        |
        v
demo-user provisioning command + Django auth session
        |
        v
GymCompletion migration and ownership constraint
        |
        v
today-toggle view and authorization tests
        |
        v
homepage weekly history and browser verification
```

## Task 1: Replace the single demo identity with two Django users

**Acceptance:** The idempotent provisioning command creates or updates two
environment-configured users with hashed passwords; Django's standard login
and logout establish the authenticated user.

**Verify:** Focused authentication tests demonstrate each account can sign in,
an invalid password fails, and no plaintext password reaches source control.

**Likely files:** `src/accounts/`, `src/dashboard/`, `.env.example`,
`compose.yml`, tests, and an ADR superseding ADR-001.

## Task 2: Establish the Gym completion persistence boundary

**Acceptance:** `GymCompletion` belongs to `settings.AUTH_USER_MODEL`; the
database rejects duplicate completions for the same user/date.

**Verify:** Model tests run against PostgreSQL and migration validation passes.

**Likely files:** `src/gym/models.py`, `src/gym/migrations/`,
`tests/application/test_gym_models.py`.

## Checkpoint: Durable, private data

- [ ] Migrations apply to an empty local database.
- [ ] Two users can hold completions independently on the same day.
- [ ] Full tests, coverage, and Django checks pass.

## Task 3: Add today's protected toggle

**Acceptance:** An authenticated POST toggles only the requesting user's
completion for the application-local current date; GET and CSRF-less requests
cannot change state.

**Verify:** View tests cover create, remove, unauthenticated redirect, CSRF,
and cross-account isolation.

**Likely files:** `src/gym/views.py`, `src/gym/urls.py`, project URLs, and
`tests/application/test_gym_views.py`.

## Task 4: Replace filler Gym information on the homepage

**Acceptance:** The homepage shows the current user's actual weekly day marks,
completed-day count, and today's checked/unchecked control. Filler Reading
content may remain visually static but does not claim persistence.

**Verify:** Template/view tests and a browser test complete the real sign-in →
toggle → refresh → logout path.

**Likely files:** `src/dashboard/views.py`, dashboard template/CSS, and
dashboard/application tests.

## Completion Checkpoint

- [ ] Each demo account's history is private and durable.
- [ ] The Gym action is keyboard accessible and server-validated.
- [ ] `pytest --cov --cov-branch --cov-fail-under=80` passes.
- [ ] Ruff, Django checks, image smoke test, and browser workflow pass.

## Risks and Mitigations

| Risk | Mitigation |
| --- | --- |
| Demo credentials leak | Use `.env` only; provision hashes with Django; inspect the diff before commit. |
| One user alters another's data | Never accept an owner field; always use `request.user`. |
| Duplicate clicks create duplicate records | Enforce the `(user, completed_on)` uniqueness constraint. |
| Late-night completion is assigned to the wrong day | Use the approved UTC application timezone and `timezone.localdate()`; per-user timezones are a future feature. |
| Scope expands into social features | Preserve friend comparison as a future feature despite the ownership-ready model. |
