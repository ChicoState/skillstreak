# Spec: Profile Settings Foundation

### Problem to solve

The application has no user-facing profile or settings page. It therefore has
no place for a user to see their account identity, set a timezone, or state
whether they want reminders before reminder behavior exists.

### Desired outcome

An authenticated user has a **Profile & settings** page that shows their email
address, lets them select an IANA timezone (default `UTC`), and lets them turn
reminders on or off (default off). Their settings persist and can affect only
their own account.

### Proposed solution

Use the existing `tracking.UserPreference` table as the preference store.
Extend it with a `reminders_enabled` boolean, retain `timezone` as an IANA
timezone name, and create a missing record lazily for the authenticated user.
Add a small `profiles` UI app with an authenticated route, form, template, and
dashboard navigation entry.

### Alternatives considered

#### Add settings to the dashboard view

Rejected. The dashboard already owns skill selection and daily completion. A
dedicated UI boundary gives future settings a stable home.

#### Move `UserPreference` to a new app now

Rejected. The existing one-to-one table already has the right ownership and
migrating it would create unrelated schema churn.

### Additional context

This is a profile foundation only. It creates no reminders, schedule
calculations, profile alert list, email backend, delivery preference, reminder
time, or password-reset behavior. It does provide an authenticated password
change flow using Django's built-in password hashing and validators. IANA names
are necessary because UTC offsets cannot safely represent daylight-saving
changes for future local-time features.

### Before submitting

- [ ] Confirm the page is authenticated and current-user-only.
- [ ] Confirm a missing preference becomes `UTC` with reminders disabled.
- [ ] Confirm invalid timezone input cannot persist.
- [ ] Confirm no reminder event, email, or schedule behavior is introduced.
- [ ] Confirm password changes require the current password and preserve the
      changing user's session.

## Status

Implemented.

## Objective

Create the application's authenticated profile and settings surface. It gives
every signed-in user a stable place to see their account email, manage their
timezone and reminder preference, and change their password.

The feature is deliberately a foundation. It does not create reminders, send
email, calculate schedules, decide where a future reminder is delivered, or
provide password recovery.

## User Experience

- A signed-in user can navigate to **Profile & settings** from the dashboard.
- The page displays the signed-in user's normalized email address as read-only
  account information.
- The page offers an IANA timezone selector. `UTC` is the default for a user
  who has never saved a preference.
- The page offers an accessible on/off reminder preference, defaulting to off.
- Saving only changes the signed-in user's own preference record; settings
  persist across refreshes and future sign-ins.
- A signed-in user can follow **Change password**, enter their current password,
  enter and confirm a new password, and return to the dashboard after saving.
- A successful password change keeps the current session authenticated while
  invalidating other sessions for that account.

## Data Contract

The existing `tracking.UserPreference` table remains the persistence source for
this slice. Add a `reminders_enabled` boolean, defaulting to `False`. Its
existing `timezone` field continues to contain an IANA zone name, with `UTC` as
its database default.

A preference record may not exist for accounts created before this feature.
The profile view must safely obtain or create the current user's record. It
must never use user-supplied ownership identifiers.

## Scope

- Authenticated profile/settings route, view, form, template, navigation, and
  authorization tests.
- Read-only display of the current user's email address.
- Persisted IANA timezone selection.
- Persisted reminder on/off preference and a persisted Green, Blue, or Purple
  color-palette choice.
- Clear validation feedback for an invalid timezone value.
- Authenticated password change using Django's `PasswordChangeForm`, including
  the configured password validators and current-password verification.

## Out of Scope

- In-profile reminder inboxes or alerts.
- Email, push, or SMS delivery.
- Reminder delivery choices, reminder time, reminder content, or escalation.
- Editing email or password reset/recovery.
- Skill scheduling, skill creation/search, social features, and account
  profile fields such as names or avatars.

## Commands

```sh
docker compose up -d db
docker compose run --rm web python manage.py migrate
docker compose exec web pytest tests/application --cov --cov-branch --cov-fail-under=80 --cov-report=term-missing
docker compose exec web ruff format --check .
docker compose exec web ruff check .
```

## Project Structure

```text
src/profiles/                 # Authenticated profile route, form, and template
src/tracking/models.py        # Existing UserPreference persistence model
src/skillstreak/urls.py       # Profile route inclusion
tests/application/            # Profile authorization and persistence tests
docs/specs/                   # User-facing acceptance criteria
docs/plans/                   # Merge-sized implementation tasks
```

## Code Style

All state changes derive ownership from the signed-in request and use a
CSRF-protected POST. The view may create a missing default preference only for
the current user:

```python
preference, _ = UserPreference.objects.get_or_create(
    user=request.user,
    defaults={"timezone": "UTC", "reminders_enabled": False},
)
```

## Testing Strategy

- PostgreSQL-backed model tests cover the default and persisted fields.
- View tests cover authentication redirects, current-user-only updates,
  validation, CSRF, and persistence after a new client session.
- Browser verification covers navigation to the settings page, saving a
  timezone and reminder preference, changing a password, and seeing saved
  values after reload.

## Boundaries

- Always: use Django migrations, validated IANA timezone values, POST + CSRF
  for updates, `request.user` for ownership, Django-managed password hashing,
  and `update_session_auth_hash` after a password change.
- Ask first: add profile fields beyond email/timezone/reminder opt-in, move the
  existing `UserPreference` table to a different Django app, add password
  recovery, or change account credential policy.
- Never: send a reminder/email from this slice, accept a user ID in the form,
  expose another user's preferences, log submitted passwords, or commit
  credentials.

## Success Criteria

- An authenticated user can reach Profile & settings from the dashboard.
- The page shows only that user's email and preferences.
- A newly created preference defaults to `UTC` and reminders disabled.
- A valid timezone and reminder choice persist after reload and sign-in.
- Invalid timezone input cannot be saved.
- Password changes require the current password, validate the new password,
  replace the old hash, preserve the current session, and invalidate other
  sessions.
- No reminder event, delivery attempt, or schedule calculation is introduced.
