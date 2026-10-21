# Implementation Plan: User XP, Levels, and Scheduled Skills

## Status

Approved — 2026-10-21.

## Overview

Implement the approved [user XP and levels specification](../specs/user-xp-and-levels.md)
as a server-rendered Django feature. An authenticated member will create
private weekly skills and complete or undo eligible dates. The dashboard will
replace sample data with that member's skills and derived account progression.

## Architecture Decisions

- Add a `skills` Django app. It owns `Skill`, weekly schedule, completion, and
  progression-calculation code; `dashboard` only orchestrates and presents it.
  The rationale is recorded in [ADR-003](../decisions/003-user-progression-history.md).
- Add a nullable, validated IANA timezone field to `accounts.User`. The
  timezone is automatically detected by browser JavaScript, submitted through a
  CSRF-protected POST, and validated on the server before persistence. The
  dashboard reloads after first detection so its dates match the stored zone.
- Store a `Skill` owner and name; store selected weekdays as separate schedule
  records with a database uniqueness constraint per `(skill, weekday)`; store
  a `Completion` as one `skill` plus one local `completed_on` date with a
  database uniqueness constraint per `(skill, completed_on)`.
- Derive `total_xp = completion_count * 10` and level from the approved
  threshold formula on every relevant query. Do not persist a duplicate XP or
  level balance.
- Determine eligible completion dates in the account's timezone. A completion
  action takes an explicit date from the server-rendered prior-seven-day range;
  it succeeds only if the date is no later than the local date, no older than
  seven local days, and scheduled for that weekday.
- Keep every feature mutation POST-only, CSRF-protected, and ownership-scoped
  to `request.user`. Wrap toggles in `transaction.atomic()` and translate
  uniqueness races into the same idempotent, correct end state.

## Delivery Order and Dependencies

```text
Account timezone migration
        │
        ├── Browser timezone synchronization
        │         │
        │         └── Local-date dashboard context
        │
Skills/schedules/completions migration
        │
        ├── Progression service (XP, levels, eligibility)
        │         │
        │         ├── Skill creation and completion views/forms/URLs
        │         │         │
        │         │         └── Dashboard data and accessible UI
        │         │
        │         └── Model, authorization, and view tests
        │
        └── Browser verification and full regression checks
```

The migrations must precede every feature path. Progression rules are built and
tested before views so the UI cannot develop its own calculation. The
dashboard is last because it consumes the completed domain interface.

## Planned Work Areas

1. **Domain and migrations** — Create the `skills` app, models, migrations,
   ownership/schedule/completion constraints, and account timezone migration.
2. **Progression service** — Centralize XP, level threshold, next-level
   progress, local-date eligibility, and completion toggle behavior in typed,
   transaction-safe domain functions.
3. **Forms and routes** — Add forms for skill name/weekdays and hidden or
   explicit completion date; add ownership-safe views and URLs. Add the
   timezone synchronization endpoint used only by the authenticated browser.
4. **Dashboard UI** — Render real skills, the preceding seven local dates,
   completion controls, an empty state, and the level/XP progress bar. Retain
   the established visual tokens and semantic, keyboard-operable controls.
5. **Verification** — Build the test suite red-first, then exercise the user
   flow in a browser at the project breakpoints and run all repository checks.

## Task Breakdown

### Phase 1: Data foundations

#### Task 1: Add account timezone support

**Description:** Add a nullable, validated IANA timezone field to the custom
account model and create the account migration without changing existing
authentication behavior.

**Acceptance criteria:**

- [x] A user can persist a valid IANA timezone or remain unset before browser
      synchronization.
- [x] Invalid timezone names are rejected by model validation.
- [x] Existing account registration and sign-in tests continue to pass.

**Verification:**

- [x] Add focused model and migration tests, then run
      `docker compose exec web pytest tests/application/test_accounts.py`.
- [x] Run `docker compose exec web python manage.py makemigrations --check`.

**Dependencies:** None.

**Files likely touched:** `src/accounts/models.py`,
`src/accounts/migrations/0002_user_timezone.py`,
`tests/application/test_accounts.py`.

**Estimated scope:** Medium (3 files).

#### Task 2: Create skills, schedules, and completions

**Description:** Add the `skills` app and PostgreSQL-backed models for owned
skills, weekday schedules, and dated completions with the required uniqueness
and ownership constraints.

**Acceptance criteria:**

- [x] Skills belong to exactly one account and schedules belong to exactly one
      skill.
- [x] Duplicate `(skill, weekday)` and `(skill, completed_on)` rows are
      rejected at the database layer.
- [x] The migration applies cleanly on PostgreSQL and does not add fixtures or
      unrelated product data.

**Verification:**

- [x] Add model and constraint tests in `tests/application/test_skills.py`.
- [x] Run `docker compose exec web pytest tests/application/test_skills.py`.
- [x] Run `docker compose exec web python manage.py migrate --noinput`.

**Dependencies:** Task 1.

**Files likely touched:** `src/skills/apps.py`, `src/skills/models.py`,
`src/skills/migrations/0001_initial.py`, `src/skillstreak/settings/base.py`,
`tests/application/test_skills.py`.

**Estimated scope:** Large (5 files).

### Checkpoint: Data foundations

- [x] Task 1 tests pass against PostgreSQL.
- [x] Task 2 tests pass against PostgreSQL.
- [x] `docker compose exec web python manage.py check` passes.
- [x] `docker compose exec web python manage.py makemigrations --check` passes
      for Tasks 1–2.

### Phase 2: Progression and mutation behavior

#### Task 3: Implement progression calculations and eligibility

**Description:** Add a focused domain service for XP totals, level thresholds,
level-cap behavior, local-date windows, scheduled-day eligibility, and atomic
completion toggling.

**Acceptance criteria:**

- [x] XP and levels match every published threshold through level 99 and
      continue accumulating XP after the cap.
- [x] Completion toggles are atomic; each toggle creates or removes one
      completion and changes derived progression by exactly 10 XP.
- [x] Eligibility uses the account's validated local timezone and rejects
      unscheduled or out-of-window dates.

**Verification:**

- [x] Add red-first unit and transaction tests in
      `tests/application/test_progression.py`.
- [x] Run `docker compose exec web pytest tests/application/test_progression.py`.

**Dependencies:** Tasks 1–2.

**Files likely touched:** `src/skills/progression.py`,
`tests/application/test_progression.py`.

**Estimated scope:** Small (2 files).

#### Task 4: Add skill creation, timezone sync, and completion routes

**Description:** Add server-validated forms, ownership-scoped POST views, URLs,
and the authenticated timezone synchronization endpoint.

**Acceptance criteria:**

- [x] Authenticated members can create a named skill with one or more
      weekdays.
- [x] Completion mutations are POST-only, CSRF-protected, ownership-scoped,
      and reject forged dates, weekdays, XP, and skill owners.
- [x] Anonymous requests redirect to sign-in and cross-account identifiers do
      not expose or mutate another member's data.

**Verification:**

- [x] Add form and view tests covering authentication, CSRF, validation, and
      cross-account isolation.
- [x] Run `docker compose exec web pytest tests/application/test_skills.py
      tests/application/test_progression.py`.

**Dependencies:** Task 3.

**Files likely touched:** `src/skills/forms.py`, `src/skills/views.py`,
`src/skills/urls.py`, `src/skillstreak/urls.py`,
`tests/application/test_skills.py`.

**Estimated scope:** Large (5 files).

### Checkpoint: Core behavior

- [x] Skill creation and completion mutation tests pass.
- [x] Anonymous access, CSRF rejection, and cross-account isolation are
      covered.
- [x] Ruff formatting and linting pass for the new domain and route code.

### Phase 3: Dashboard and release verification

#### Task 5: Replace sample dashboard data with account-owned progress

**Description:** Update dashboard orchestration and templates to display the
authenticated member's skills, the prior seven local dates, completion state,
and derived XP/level progress, including an empty state and timezone-sync
behavior.

**Acceptance criteria:**

- [ ] Static Jogging, Reading, sample calendar, and sample progression values
      are removed from the rendered dashboard.
- [ ] The dashboard displays only the signed-in member's skills and derived
      progression, with accessible POST completion controls.
- [ ] The layout remains usable at 320px, 768px, 1024px, and 1440px.

**Verification:**

- [ ] Update dashboard integration tests to prove owner-only rendering and
      empty-state behavior.
- [ ] Run the authenticated flow in a real browser, including keyboard use,
      skill creation, completion toggling, and visible XP/level updates.

**Dependencies:** Task 4.

**Files likely touched:** `src/dashboard/views.py`,
`src/dashboard/templates/dashboard/preview.html`,
`src/dashboard/static/dashboard/styles.css`,
`tests/application/test_dashboard.py`.

**Estimated scope:** Medium (4 files).

#### Task 6: Run complete verification and document the finished slice

**Description:** Run the full repository checks, resolve regressions, and
update the project documentation to describe the implemented user-owned
progression behavior and verification workflow.

**Acceptance criteria:**

- [ ] Django tests, coverage, Ruff, infrastructure checks, image smoke test,
      PostgreSQL smoke test, and browser verification pass.
- [ ] Documentation no longer claims that user-owned skill/progress behavior
      is absent.
- [ ] The final diff contains no secrets, generated reports, local volumes, or
      build artifacts.

**Verification:**

- [ ] Run `docker compose exec web pytest`.
- [ ] Run `docker compose exec web ruff format --check .` and
      `docker compose exec web ruff check .`.
- [ ] Run `./scripts/check-infrastructure.sh`, `./scripts/smoke-image.sh`,
      `./scripts/smoke-postgres.sh`, and `git diff --check`.

**Dependencies:** Task 5.

**Files likely touched:** `README.md`, `AGENTS.md`, and affected test or
documentation files identified during verification.

**Estimated scope:** Medium (up to 5 files per focused correction).

### Checkpoint: Complete

- [ ] All specification success criteria pass.
- [ ] All task acceptance criteria are checked off.
- [ ] The implementation is ready for human review before merge.

## Security and Abuse Cases

| Case | Control | Verification |
| --- | --- | --- |
| Member submits another member's skill ID | Query feature objects by ID and `owner=request.user` | Expect 404/no state change |
| Duplicate or concurrent completion requests | Database unique constraint plus atomic toggle | Exactly one completion and 10 XP |
| Browser submits an arbitrary date | Server compares against account-local seven-day window and schedule | Invalid dates rejected/no state change |
| Browser lies about weekday or XP | Server derives weekday, XP, and level | Submitted values cannot affect result |
| Invalid timezone name | Validate against IANA database before persisting | No local-date mutation until valid |
| CSRF-less state-changing request | Django CSRF middleware and test coverage | Expect 403 |

## Risks and Mitigations

| Risk | Impact | Mitigation |
| --- | --- | --- |
| Browser timezone is absent or unavailable | Local date is ambiguous | Block completion controls until automatic detection succeeds and show a concise recovery state. |
| Timezone changes while travelling | Wrong eligible-day calculation | Synchronize the detected zone on authenticated dashboard load and include it with mutations; server validates before use. |
| Date boundaries and daylight-saving changes | Incorrect week window | Use Python timezone-aware local-date conversion, never fixed UTC offsets; test a non-UTC zone. |
| Schedule edits rewrite history | Confusing historical eligibility | Editing schedules is out of scope; initial slice creates schedules only. |
| Aggregate XP eventually becomes costly | Slower dashboard reads | Start derived for correctness; profile before adding an explicitly documented cache. |

## Verification Checkpoints

### Domain checkpoint

- Migrations apply on PostgreSQL.
- Tests cover thresholds 0–99, post-cap XP, duplicate completion prevention,
  undo, dates at both seven-day boundaries, schedules, and a non-UTC timezone.
- `docker compose exec web pytest` and Ruff checks pass.

### Integration checkpoint

- Tests prove authenticated creation/toggling, anonymous redirects, CSRF
  rejection, and cross-account isolation.
- A dashboard test proves static sample values are absent and only owner data
  appears.

### Browser checkpoint

- In a real browser, automatic timezone detection enables the flow; adding a
  skill and toggling a scheduled date visibly changes XP/level.
- Controls work by keyboard and remain usable at 320px, 768px, 1024px, and
  1440px.

### Complete checkpoint

- `./scripts/check-infrastructure.sh`
- `./scripts/smoke-image.sh`
- `./scripts/smoke-postgres.sh`
- `git diff --check`
- Review the final diff for secrets and generated files.

## Open Questions

None. The task breakdown is approved by the plan approval recorded above;
implementation may begin one task at a time.
