# Implementation Plan: User XP, Levels, and Scheduled Skills

## Status

Draft — awaiting plan approval.

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

None. The next gated phase is task breakdown after human approval of this plan.
