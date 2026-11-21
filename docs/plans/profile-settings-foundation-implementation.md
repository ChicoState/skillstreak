# Implementation Plan: Profile Settings Foundation

### Problem to solve

Profile preferences and authenticated credential changes need a durable, tested
implementation path without adding reminder delivery or password recovery.

### Desired outcome

Ship the profile-settings foundation in independently reviewable merges while
preserving the existing account, dashboard, and tracking behavior.

### Proposed solution

Implement preference persistence and validation, then the authenticated UI,
dashboard navigation, and password-change flow.

### Alternatives considered

#### One large profile merge

Rejected. Separating persistence from the UI makes the migration and
ownership/validation rules reviewable before presentation changes.

### Additional context

This plan implements [Profile Settings Foundation](../specs/profile-settings-foundation.md).
`UserPreference` remains in `tracking` for this feature; `profiles` is a UI
boundary, not a duplicate persistence model. Password changes use Django's
built-in `PasswordChangeForm` and require no schema migration.

### Before submitting

- [ ] Run migrations against an empty PostgreSQL database.
- [ ] Run focused model/form/view authorization tests.
- [ ] Run the application test/coverage command and Ruff checks.
- [ ] Confirm this work creates no reminder delivery path.

## Status

Implemented. Implements [Profile Settings Foundation](../specs/profile-settings-foundation.md).

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
- Keep password changes in `profiles` as an authenticated UI flow while
  delegating current-password verification, password validation, hashing, and
  password-session handling to Django's built-in authentication APIs.

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

## Merge 3: Authenticated Password Change

**Description:** Add a protected password-change page linked from Profile &
settings. The form requires the current password, validates and confirms the
new password through Django, preserves the changing session, and invalidates
other sessions.

**Acceptance criteria:**

- [x] Only authenticated users can view or submit the password-change form.
- [x] The form uses Django's `PasswordChangeForm` without replacing its
      validation or save behavior.
- [x] A successful change redirects to the dashboard and preserves the current
      session; the old password fails and the new password succeeds.
- [x] Failed validation leaves the existing password unchanged.
- [x] Password changes are CSRF-protected and derive ownership from
      `request.user` only.

**Verification:**

- [x] Application tests cover replacement, validation, CSRF, isolation, and
      concurrent-session behavior.
- [x] Browser verification covers settings navigation, password replacement,
      logout, old-password rejection, and new-password sign-in.

**Likely files:** `src/profiles/forms.py`, `src/profiles/views.py`,
`src/profiles/urls.py`, `src/profiles/templates/`, and application/browser
tests.

## Risks and Mitigations

| Risk | Mitigation |
| --- | --- |
| Invalid timezone causes future date bugs | Validate against Python's IANA timezone database; store only canonical choices. |
| Existing users lack a preference row | Lazily `get_or_create` one for `request.user`. |
| Settings become accidental reminder behavior | Keep model fields and UI preference-only; no background work, reminder query, or email backend in scope. |
| Password change bypasses framework security | Wrap Django's `PasswordChangeForm` without redefining its fields or validation; test current-password verification, hashing, CSRF, and session behavior. |
