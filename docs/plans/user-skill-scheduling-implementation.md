# Implementation Plan: User Skill Scheduling

### Problem to solve

The application needs a safe implementation sequence for user-selected skill
schedules without coupling schedule work to reminders, email, search, custom
skills, or social features.

### Desired outcome

Implement all agreed schedule choices in small merges, with a reusable,
well-tested expected-date evaluator available before dashboard forms depend on
it.

### Proposed solution

Build the dependency chain bottom-up: schedule rules and evaluator, then
add-skill setup, then schedule display/editing.

### Alternatives considered

#### Build all schedule UI before the evaluator

Rejected. A shared evaluator is the correctness boundary future reminders will
need; putting it first avoids duplicate rule logic in forms and dashboard code.

#### Deliver all schedule behavior in one merge

Rejected. It combines a migration, complex date logic, creation UI, editing
UI, and browser behavior into one review surface.

### Additional context

This plan implements [User Skill Scheduling](../specs/user-skill-scheduling.md)
after profile settings. Schedule behavior belongs to `UserSkill`, never to the
shared `Skill`, because users may choose different cadences for the same skill.

### Before submitting

- [ ] Preserve the PostgreSQL non-overlapping schedule-range guarantee.
- [ ] Run focused tests after every merge before continuing.
- [ ] Keep all dates user-local and all ownership derived from `request.user`.
- [ ] Confirm the change does not generate reminders or emails.

## Status

Planned. Implements [User Skill Scheduling](../specs/user-skill-scheduling.md)
after the profile-settings foundation is available.

## Architecture Decisions

- Schedule behavior belongs to the selected skill (`UserSkill`), not the
  shared system `Skill`, because two users may follow the same skill at
  different cadences.
- Keep the existing dated schedule-history model. Do not overwrite a schedule
  on edit; close the previous effective range and create the next range.
- Continue to use one `DailyCompletion` per local date. An intended daily
  occurrence count describes future capability and does not multiply current
  completions.
- Keep time slots out of this UI. A later occurrence table can reference a
  schedule and an occurrence index without changing the binary completion
  contract.
- The schedule evaluator must be a reusable domain service rather than logic
  copied into views. Reminder work will depend on the same answer.

## Dependency Graph

```text
Profile timezone setting
        |
        v
schedule model validation + migration
        |
        v
local-date expected-occurrence evaluator
        |
        +-----------------------+
        v                       v
add-skill schedule setup    future-dated schedule editing
        |                       |
        +-----------+-----------+
                    v
       dashboard schedule display and verification
```

## Merge 1: Schedule Rules and Local-Date Evaluator

**Description:** Finish model/migration support for the agreed schedule shapes
and introduce a tested service for evaluating whether a skill is expected on a
given local date. No dashboard controls change in this merge.

**Acceptance criteria:**

- [ ] Rule-specific validation covers daily, intended multiple daily
      occurrences, every-other-day, weekly/biweekly weekday rules, selected
      weekdays, selected month dates, and last-day monthly rules.
- [ ] The evaluator handles start dates, effective ranges, leap years, and
      skipped short-month dates.
- [ ] The evaluator uses the owning user's configured IANA timezone.

**Verification:**

- [ ] Focused model/service tests pass against PostgreSQL.
- [ ] `docker compose run --rm web python manage.py migrate --plan` is
      reviewed before applying.

**Likely files:** `src/tracking/models.py`, `src/tracking/migrations/`, a
new `src/tracking/scheduling.py`, and scheduling tests.

## Merge 2: Add-Skill Schedule Setup

**Description:** Replace the direct library add action with an authenticated
schedule setup flow. It defaults to daily, today, and validates the additional
fields required by the selected schedule type.

**Acceptance criteria:**

- [ ] Adding a skill creates the `UserSkill` and its first schedule together.
- [ ] Users can select all approved schedule types and only today/future start
      dates.
- [ ] A month-date selection warns about skipped short months and exposes Last
      day as a separate explicit choice.

**Verification:**

- [ ] View/form tests cover each schedule type, validation errors, ownership,
      and CSRF.
- [ ] Browser check adds a skill using the default daily schedule and one
      non-daily schedule.

**Likely files:** tracking views/forms/URLs/templates, dashboard library UI,
and application tests.

## Merge 3: Schedule Display and Future-Dated Editing

**Description:** Display each active skill's schedule and permit the owner to
create a replacement schedule effective today or later.

**Acceptance criteria:**

- [ ] The dashboard clearly displays the active schedule.
- [ ] An edit closes the preceding range without overlap and preserves past
      records.
- [ ] Editing another user's selection returns 404; past dates are rejected.

**Verification:**

- [ ] Model/view tests cover same-day replacement, future replacement, and
      cross-account isolation.
- [ ] Browser check edits a schedule, reloads, and confirms its future
      effective date.

**Likely files:** tracking views/forms/templates, dashboard context/template,
and application tests.

## Checkpoints

### After Merge 1

- [ ] The evaluator is independently tested for every rule before UI work
      relies on it.
- [ ] No reminder state, email backend, or profile reminder preference is
      added.

### After Merge 3

- [ ] Full application tests, 80% coverage, Ruff formatting, and Ruff lint
      pass.
- [ ] Browser workflow proves add and edit behavior in a real authenticated
      session.
- [ ] Existing selection and binary completion tests still pass.

## Risks and Mitigations

| Risk | Mitigation |
| --- | --- |
| Existing model constraints do not represent every requested rule cleanly | Write rule/evaluator tests before migration changes; update constraints in the same migration. |
| A same-day edit causes overlapping schedules | Treat same-day replacement as an update of the not-yet-historical current range; test PostgreSQL exclusion behavior. |
| Daily completion remains tied to UTC | Make the user-local-date boundary explicit in the profile dependency and evaluator tests before changing dashboard completion behavior. |
| Multiple daily occurrences invite premature notification scope | Persist only the intended count; defer slots, occurrence completions, and notifications. |
