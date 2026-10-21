# Spec: User XP, Levels, and Scheduled Skills

## Status

Approved — 2026-10-14.

## Objective

Give each authenticated SkillStreak member a private, persistent skill routine and
visible progression. A member creates a skill, selects the weekdays on which it
is due, and marks its scheduled completion for a date. Each valid completion
awards 10 XP; undoing that completion removes 10 XP. Total XP determines the
account's level and the dashboard shows current level and progress toward the
next level.

### User stories

- As a signed-in member, I can create a skill and choose its weekly schedule.
- As a signed-in member, I can mark a skill complete on a day it is scheduled
  so that I receive 10 XP.
- As a signed-in member, I can undo a completion and see the earned XP and
  level update correctly.
- As a signed-in member, I can see my total XP, current level, and progress to
  the next level on my dashboard.

### XP and level rules

- One completion belongs to exactly one owner, one skill, and one calendar
  date. A skill can earn XP only once per date.
- A completed scheduled skill/date earns exactly 10 XP. Undoing it removes
  exactly 10 XP.
- Account XP is the total XP from the account's current completions. The level
  is derived from that total; a toggle is atomic so stored progression cannot
  drift from completion history.
- Level 0 begins at 0 XP. The total-XP thresholds are: level 1 = 10, level 2
  = 20, level 3 = 40, level 4 = 70, level 5 = 110, level 6 = 160, and level 7
  = 220. Thereafter, each next threshold adds 10 XP more than the preceding
  threshold gap: the threshold for level _n_ is `10 + 10 * (n - 1) * n / 2`.
  The threshold for level 99 is 48,520 XP.
- Level 99 is the maximum level. Further completions continue to increase the
  account's total XP, but never increase the level beyond 99.
- Each account has a validated IANA timezone preference. Scheduled weekday and
  completion-date eligibility use the account's local calendar date, rather
  than the server's UTC date.
- On first authenticated use, the browser detects its IANA timezone and submits
  it for persistence. The server validates it against the available IANA zone
  database; missing or invalid values must not authorize a completion whose
  local date cannot be determined.

## Scope

- Persist user-owned skills, their selected weekly weekdays, and completions.
- Add an authenticated dashboard flow to create skills and mark or undo a
  scheduled completion on the current or previous seven local calendar days.
- Replace static sample skill/progress figures with only the signed-in
  account's records and calculated XP/level display.
- Use Django forms, server-rendered HTML, POST requests with CSRF protection,
  and PostgreSQL-backed Django migrations.

## Out of Scope

- Sharing skills or progress, public profiles, social features, notifications,
  goals beyond selected weekdays, custom XP values, badges, achievements,
  APIs, imports/exports, or calendar integrations.
- Password, session, email-domain, or account-registration changes.
- Level rewards, timezone changing, and historical editing beyond the prior
  seven local calendar days.

## Tech Stack

- Python 3.14, Django 5.2 LTS, PostgreSQL, pytest with pytest-django, and
  server-rendered Django templates.
- Existing `accounts` app remains the account source of truth. A focused
  application model boundary for skills/progression will be selected in the
  approved implementation plan.

## Commands

```sh
docker compose up --build
docker compose exec web python manage.py makemigrations
docker compose exec web python manage.py migrate
docker compose exec web pytest
docker compose exec web ruff format --check .
docker compose exec web ruff check .
./scripts/check-infrastructure.sh
./scripts/smoke-image.sh
./scripts/smoke-postgres.sh
git diff --check
```

## Project Structure

```text
src/accounts/                 Email-only authenticated account model
src/<feature-app>/            Skill, schedule, completion, and XP domain code
src/dashboard/                Authenticated dashboard views, template, and CSS
tests/application/            Model, form, view, authorization, and XP tests
docs/specs/                   Approved feature specifications
docs/plans/                   Approved implementation plan and task breakdown
```

## Code Style

Follow the project's typed Python, Ruff formatting, small focused Django views,
and descriptive tests. All state-changing requests use server-validated forms
and derive the owner from `request.user`, never a submitted identifier.

```python
@login_required
@require_POST
def toggle_completion(request: HttpRequest, skill_id: int) -> HttpResponse:
    skill = get_object_or_404(Skill, pk=skill_id, owner=request.user)
    completion, created = Completion.objects.get_or_create(
        skill=skill,
        completed_on=localdate(),
    )
    if not created:
        completion.delete()
    refresh_progression(request.user)
    return redirect("dashboard-preview")
```

The approved implementation may refine this example, but must preserve its
ownership check, POST-only mutation, CSRF protection, and atomic progression
update.

## Testing Strategy

- Write model and XP/level tests first: thresholds, level 0, level 99, a
  completion award, undo, and a duplicate skill/date attempt.
- Add Django integration tests for skill creation, weekday validation,
  scheduled-day eligibility, dashboard rendering, and persistence.
- Add authorization and abuse-case tests proving one member cannot read or
  change another member's skills, completions, XP, or level.
- Add focused browser verification for keyboard-operable form controls,
  completion toggling, XP/level updates, and the 320px, 768px, 1024px, and
  1440px layouts.
- Run the full project suite, Ruff checks, required infrastructure smoke
  checks, and `git diff --check` before handoff.

## Boundaries

- Always: enforce ownership in every query and mutation; validate all form
  input server-side; use POST plus CSRF protection for changes; use Django ORM
  and transactions; retain Django template auto-escaping; calculate or
  transactionally refresh XP and level from completion state; keep controls
  semantic and keyboard-operable.
- Ask first: add dependencies, change CI or delivery configuration, change
  authentication/session behavior, collect new sensitive data, add external
  integrations, alter progression rules, or broaden editing/history scope.
- Never: trust an owner/account identifier from a browser form, grant XP for
  duplicate or unscheduled completions, expose another member's data, commit
  credentials, remove tests to obtain a passing build, or modify unrelated
  infrastructure.

## Success Criteria

- An authenticated member can create a skill with one or more selected weekly
  weekdays; an anonymous visitor cannot access or mutate feature data.
- On an eligible date, the member can mark their own skill complete once; it
  contributes exactly 10 XP and appears as complete on the dashboard.
- Undoing that completion removes exactly 10 XP and recalculates level and
  progress correctly. Repeated toggles never create duplicate completions or
  double-award XP.
- A member can only create or undo a completion dated today or within the
  preceding seven local calendar days. Dates outside that window are rejected
  server-side.
- The dashboard displays only the signed-in member's skills and progression.
- Level transitions follow the published cumulative threshold formula through
  level 99; test coverage includes the listed milestones and continued XP
  accrual at the level cap.
- A member cannot access or change another member's skills, completions, XP,
  or level by modifying URLs or submitted fields.

## Open Questions

None. This draft is ready for product approval.
