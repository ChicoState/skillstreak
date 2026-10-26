# Spec: User Skill Scheduling

### Problem to solve

As a user, I want to select different schedules for my skills instead of just
daily.

### Desired outcome

When adding a skill, a user chooses a schedule, defaulting to daily. Supported
schedules are daily, multiple times a day, every other day, once a week, every
other week, multiple days of a week, specific days of a month, and last day of
every month. The user can later edit the schedule without rewriting history.

### Proposed solution

Use the existing selected-skill schedule tables as the history source of
truth. Add schedule setup to skill addition, a future-dated edit flow for
active skills, and a reusable local-date evaluator.

For multiple-times-daily schedules, ask for an intended occurrence count. One
completion still satisfies the whole local day for now. Store the intended
count and preserve a future path for time slots and occurrence-level mobile
reminders without collecting slots or creating multiple daily completions.

For monthly dates absent from shorter months, warn that the date is skipped and
offer **Last day of every month** as an explicit alternative rather than an
automatic fallback.

### Alternatives considered

#### Keep all skills implicitly daily

Rejected. It prevents users from accurately defining their routines and gives
future missed-period/reminder work an incorrect foundation.

#### Create one completion per daily occurrence now

Rejected for this slice. The tracker remains binary per day; occurrence
records and notifications would expand both data and UI scope.

#### Treat a short-month date as the last day automatically

Rejected. A literal 31st should skip months without a 31st. Last-day behavior
must be an intentional user choice.

### Additional context

The repository already has `UserSkillSchedule`, weekday, and month-day schema
but no schedule creation/editing UI or expected-date evaluator. This feature
depends on profile settings so dates consistently use the user's IANA timezone.
It adds no reminders, emails, escalation, search, custom skill creation, or
social behavior.

### Before submitting

- [ ] Verify every schedule type can be created and displayed.
- [ ] Verify start/effective dates reject the past and preserve history.
- [ ] Verify short-month, leap-year, weekday, and biweekly cases.
- [ ] Verify one completion still satisfies a multi-times-daily schedule.
- [ ] Verify no reminders or email behavior is introduced.

## Status

Planned. Depends on the profile-settings foundation so expected dates can use
the user's configured local timezone.

## Objective

When a user adds a system skill, ask when they expect to complete it. The
schedule is durable, editable, and serves as the future source for determining
missed periods. This feature does not create reminders.

## User Experience

- Adding a skill opens schedule setup instead of immediately activating it.
- The initial schedule defaults to daily and starts today. Users may choose a
  future start date, but never a past date.
- A user can later edit an active skill's schedule. The edit takes effect
  today by default or on a chosen future date; it never rewrites historical
  schedules or completion records.
- Schedule choices are:
  - daily;
  - multiple times each day, with an intended occurrence count;
  - every other day;
  - once a week, choosing a weekday;
  - every other week, choosing a weekday;
  - multiple selected weekdays;
  - selected days of each month; or
  - the last day of every month.
- Selecting dates such as the 31st warns that the date is skipped in shorter
  months and offers the explicit Last day of every month schedule instead.

## Current Completion Semantics

Completion remains binary per skill and local calendar day. One completion
satisfies all intended occurrences for a multiple-times-daily schedule. The
schedule stores the intended daily count, but does not collect time slots or
create multiple completions/reminders per day in this version.

The design must preserve a future path for scheduled time slots and
occurrence-level mobile reminders. That future path must not alter the binary
daily tracker now.

## Data Contract

The existing `UserSkillSchedule` and weekday/month-day tables remain the
schedule-history source of truth. Extend their validation and storage only as
needed for the intended daily occurrence count and the explicit last-day
monthly choice.

There must be no overlapping effective schedule ranges for the same selected
skill. When an edit starts on a later date, the previous range ends the day
before it. Schedule occurrences are evaluated using the user's IANA timezone.

## Scope

- Schedule setup while adding an existing system skill.
- Schedule display and edit controls for the user's active skills.
- Validated persistence for every supported schedule type and effective date.
- A tested service that determines whether an active skill is expected on a
  particular local date.
- Continued binary daily completion behavior.

## Out of Scope

- Custom user-created skills, skill searching, and social behavior.
- Reminders, reminder inboxes, email, delivery timing, and escalation.
- Multiple completion records per day.
- Individual time-slot selection or occurrence-level tracking.
- Retroactive schedule edits or edits to another user's selection.

## Commands

```sh
docker compose up -d db
docker compose run --rm web python manage.py migrate
docker compose exec web pytest tests/application --cov --cov-branch --cov-fail-under=80 --cov-report=term-missing
docker compose exec web ruff format --check .
docker compose exec web ruff check .
```

## Code Style

Ownership comes from the authenticated selection, never from form input. A
schedule edit only takes effect on today or a future local date:

```python
user_skill = get_object_or_404(
    UserSkill,
    pk=user_skill_id,
    user=request.user,
    is_active=True,
)
```

## Testing Strategy

- PostgreSQL-backed model tests cover rule-specific constraints, dates,
  effective-range non-overlap, and schedule edits.
- Pure/service tests cover expected-date evaluation for every rule, leap years,
  short months, weekly anchors, and user-local dates.
- View tests cover add/edit authorization, CSRF, future-only dates, and
  persisted schedule display.
- Browser verification covers adding a skill with its default schedule and
  changing it to each schedule family.

## Boundaries

- Always: preserve schedule history, use PostgreSQL migrations, validate all
  schedule-specific fields, use local user dates, and protect updates with
  POST + CSRF.
- Ask first: add schedule rule types beyond the listed set, add time-slot UI,
  change binary completion semantics, or change a schedule retroactively.
- Never: generate reminders, silently alter prior history, create a schedule
  for another user, or accept a past effective date.

## Success Criteria

- Adding an active skill always produces an initial valid schedule.
- Every listed schedule type can be created, displayed, and edited.
- Schedule updates preserve a non-overlapping history.
- A local-date evaluator returns expected/not expected correctly for every
  supported rule, including skipped dates and last-day monthly schedules.
- One daily completion continues to satisfy a multiple-times-daily schedule.
