# Implementation Plan: Profile Settings Foundation

### Problem to solve

Profile preferences need a durable, tested implementation path without adding
any reminder delivery behavior.

### Desired outcome

Ship the profile-settings foundation in independently reviewable merges while
preserving the existing account, dashboard, and tracking behavior.

### Proposed solution

Implement preference persistence and validation first, then the authenticated
UI and dashboard navigation.

### Alternatives considered

#### One large profile merge

Rejected. Separating persistence from the UI makes the migration and
ownership/validation rules reviewable before presentation changes.

### Additional context

This plan implements [Profile Settings Foundation](../specs/profile-settings-foundation.md).
`UserPreference` remains in `tracking` for this feature; `profiles` is a UI
boundary, not a duplicate persistence model.

### Before submitting

- [ ] Run migrations against an empty PostgreSQL database.
- [ ] Run focused model/form/view authorization tests.
- [ ] Run the application test/coverage command and Ruff checks.
- [ ] Confirm this work creates no reminder delivery path.

## Status

Planned. Implements [Profile Settings Foundation](../specs/profile-settings-foundation.md).

## Architecture Decisions

- Keep `tracking.UserPreference` as the persistence model for this slice. It
  already owns the one-to-one user preference table; moving it would add
  migration churn unrelated to user-visible profile settings.
- Add a small `profiles` UI app rather than placing profile behavior in
  `accounts` or `dashboard`. This gives settings a stable home without turning
  authentication or the dashboard into a catch-all module.
- Create preference rows lazily for the authenticated user. This supports all
  existing accounts without a data migration or a fragile account-creation
  signal.
- Store an IANA zone identifier, not an offset. Offsets fail across daylight
  saving changes and cannot later support local reminder times correctly.

## Dependency Graph

```text
UserPreference timezone + reminders_enabled migration
                     |
                     v
        profile form validation and ownership rules
                     |
                     v
      authenticated Profile & settings route and navigation
                     |
                     v
     persistence, authorization, and browser verification
```

## Merge 1: Preference Persistence and Validation

**Description:** Extend the existing preference model with the disabled-by-
default reminder flag and add a profile form that accepts only known IANA
timezone values.

**Acceptance criteria:**

- [ ] Migration adds `reminders_enabled=False` without changing existing
      timezone values.
- [ ] The form accepts valid IANA names and rejects unknown values.
- [ ] A missing record can be created with `UTC` and reminders disabled.

**Verification:**

- [ ] Focused PostgreSQL model/form tests pass.
- [ ] `docker compose run --rm web python manage.py migrate --plan` shows only
      the expected migration.

**Likely files:** `src/tracking/models.py`, `src/tracking/migrations/`,
`src/profiles/forms.py`, `tests/application/test_profiles.py`.

## Merge 2: Authenticated Profile Page

**Description:** Add the protected settings route, template, and dashboard
navigation, then connect the form to the current user's preference record.

**Acceptance criteria:**

- [ ] Anonymous requests redirect to sign-in.
- [ ] The page displays the current user's email read-only.
- [ ] A CSRF-protected POST updates only the authenticated user's preferences.
- [ ] Saved values display after reload.

**Verification:**

- [ ] Focused view tests cover redirect, CSRF, persistence, and cross-account
      isolation.
- [ ] Browser check signs in, changes timezone/toggle, saves, and reloads.

**Likely files:** `src/profiles/views.py`, `src/profiles/urls.py`,
`src/profiles/templates/`, `src/skillstreak/urls.py`, dashboard navigation,
and application tests.

## Checkpoint

- [ ] Apply migrations to an empty PostgreSQL database.
- [ ] Run the application tests and 80% coverage command.
- [ ] Run Ruff format/lint checks.
- [ ] Manually confirm the profile page cannot create or deliver reminders.

## Risks and Mitigations

| Risk | Mitigation |
| --- | --- |
| Invalid timezone causes future date bugs | Validate against Python's IANA timezone database; store only canonical choices. |
| Existing users lack a preference row | Lazily `get_or_create` one for `request.user`. |
| Settings become accidental reminder behavior | Keep model fields and UI preference-only; no background work, reminder query, or email backend in scope. |
