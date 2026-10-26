# In-App Per-Skill Missed State

### Problem to solve

Users need a clear in-app indication when they have missed scheduled skill work
and a profile-level summary of those misses. The dashboard and profile own
presentation, while a reusable domain service owns missed-state calculation.

### Desired outcome

Each opted-in user's scheduled skill independently gains a missed state after
its first missed scheduled period. The dashboard shows a missed icon on that
skill until the user marks that skill completed.

Profile & settings also shows a dismissible digest of currently missed skills.
Dismissing the digest does not resolve any skill or remove its icon. The digest
stays hidden until another skill enters a new missed episode, then shows the
current unresolved misses again.


### Proposed solution

Introduce a durable per-`UserSkill` missed-state/episode record plus a
reconciliation service. The service uses the schedule evaluator and the
user's timezone to detect newly missed scheduled periods and update the active
episode. Persist a user-level digest-dismissal marker separately from skill
episodes so acknowledgement cannot alter missed state.

#### Miss detection and in-app state

- A scheduled occurrence is missed only after its local calendar day ends at
  midnight without a completion.
- The first missed period creates an active per-skill missed state; the
  dashboard then renders a missed icon on that skill.
- Completing that skill closes the active episode and resets its count.
- Reminder opt-out closes all of the user's active missed states. Re-enabling
  starts a fresh observation window, never a historical backlog.

#### Profile digest and dismissal

- The profile digest lists every currently active missed skill whenever it is
  visible.
- Dismissing the digest hides it without resolving any episode or removing a
  dashboard icon.
- A newly opened missed episode after dismissal makes the digest visible again.
- When it reappears, the digest lists all currently active missed skills, not
  only the newly missed skill.

### Alternatives considered

#### Keep the profile digest visible until all missed state clears

Rejected. Users need to be able to acknowledge the summary without falsely
resolving missed work. A new missed skill makes the digest visible again.

#### Show an icon only after three misses

Rejected. The dashboard should provide a gentle signal after the first miss;
any later escalation threshold is outside this in-app slice.

#### Count a daily skill as missed at the configured reminder time

Rejected. A daily skill becomes missed only when its local day ends at
midnight. A later same-day completion therefore remains possible without
prematurely creating a missed period.

#### Reconstruct old missed history when reminders are enabled

Rejected. Opting in starts a new observation window; users must not receive an
immediate backlog of reminders for earlier inactivity.

### Additional context

This feature follows profile settings and user skill scheduling. It relies on
their timezone, reminder opt-in value, and expected-date evaluator.

It intentionally excludes email/provider integration, email eligibility and
escalation, email content choices, configurable reminder time, background
scheduling infrastructure, persistent notification inboxes beyond this single
profile message, and mobile occurrence/time-slot reminders.

## Current MVP limit

The application reconciles missed periods when an opted-in member opens the
dashboard or profile settings. It does not yet run a background scheduler, so
an icon is created on the member's next signed-in visit rather than pushed at
midnight while they are away.

### Before submitting

- [ ] Confirm first-miss icons appear only for opted-in users after midnight.
- [ ] Confirm only completion closes that skill's missed episode.
- [ ] Confirm opt-out closes active state and re-opt-in starts fresh.
- [ ] Confirm all current-user ownership and state changes are protected.

## Data contract

The implementation needs a durable active missed episode per selected skill,
including at least the first/most recent missed local date, consecutive-miss
count, and closure state.
Completed episodes are retained as closed history rather than used as active
dashboard state.

At most one active episode may exist for a `UserSkill`. The database, not only
application code, must enforce that invariant.

A separate user-level dismissal marker records when the profile digest was last
dismissed. Visibility is derived from whether any active episode began after
that marker; it does not modify the episode records themselves.

## Acceptance criteria

- An opted-in scheduled skill shows a missed icon after its first local-day
  miss.
- A completion removes that icon and starts a new future observation window for
  that skill.
- A reminder opt-out removes all active missed icons/state for that user.
- The reconciliation service is idempotent for a user and local date.
- A user can dismiss the profile digest without clearing an icon or resolving a
  missed episode.
- The digest remains hidden after dismissal and reappears only when a new skill
  enters a missed episode, listing all current unresolved missed skills.
- One user cannot inspect or alter another user's missed state.

## Verification

```sh
docker compose up -d db
docker compose run --rm web python manage.py migrate
docker compose exec web pytest tests/application --cov --cov-branch --cov-fail-under=80 --cov-report=term-missing
docker compose exec web ruff format --check .
docker compose exec web ruff check .
```

Use PostgreSQL-backed model tests for the single-active-episode invariant,
pure/service tests for timezone boundaries and consecutive-miss counting,
protected view tests for completion and digest dismissal, and a browser check
for dashboard icon and profile-digest behavior.
