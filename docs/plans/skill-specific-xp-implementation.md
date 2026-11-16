# Implementation Plan: Skill-Specific XP

## Overview

Add derived XP, level, and progress values for each owned or selected skill.
The existing account-wide progression remains derived from both completion
models and continues to determine the account level. The two completion
schemas remain separate; a shared progression service supplies the common
calculation and the dashboard presents a skill level on landing cards plus a
skill XP bar in the selected-skill detail view.

## Architecture Decisions

- Extend the existing progression domain service rather than adding stored XP
  or level columns. This keeps undo, archival, and historical completion
  behavior self-healing.
- Keep `skills.Completion` and `tracking.DailyCompletion` separate. Their
  identifiers are not interchangeable; service functions accept authorized
  model instances/querysets rather than a browser-supplied generic skill ID.
- Compute skill levels with the existing `level_threshold` and
  `level_for_xp` rules, independently per skill, including the level-99 cap.
- Preserve archived/private completion history in derived calculations and
  account totals. No migration is expected.
- Use the dashboard's existing authorization-filtered objects as the UI seam:
  landing cards receive a skill progression, and selected detail receives the
  full skill progression needed for its XP bar.

## Dependency Graph

```text
shared progression calculation
        │
        ├── account-owned skill progression + tests
        ├── selected system/private skill progression + tests
        │             │
        │             └── dashboard context
        │                         │
        │                         ├── landing-card level
        │                         └── selected-detail XP bar
        │
        └── account-total regression tests
```

## Task List

### Phase 1: Progression foundation

- [x] Task 1: Add shared skill progression value and calculation helpers
  - Acceptance: A skill progression result contains completion count, total
    XP, current skill level, level-start XP, next-level XP, and bounded
    progress percentages; zero XP and the level-99 cap follow existing rules.
  - Verify: Add focused unit tests for zero, one, multiple, threshold, and
    capped skill XP; run `docker compose run --rm web pytest tests/application/test_progression.py`.
  - Files: `src/skills/progression.py`,
    `tests/application/test_progression.py`

- [x] Task 2: Connect both completion domains to the shared service
  - Acceptance: Account-owned skills count `skills.Completion` records and
    selected skills count `tracking.DailyCompletion` records; unauthorized or
    unrelated records are excluded; account XP still equals the sum of skill
    XP values.
  - Verify: Add cross-domain and cross-account regression tests; run
    `docker compose run --rm web pytest tests/application/test_progression.py tests/application/test_dashboard.py`.
  - Files: `src/skills/progression.py`,
    `tests/application/test_progression.py`

### Checkpoint: Progression foundation

- [x] No schema or dependency changes are introduced.
- [x] Existing account-level threshold, cap, completion, and undo tests pass.
- [x] The service shape was reviewed before dashboard changes began.

### Phase 2: Dashboard presentation

- [x] Task 3: Add skill level data to dashboard landing cards
  - Acceptance: Every authorized active dashboard card exposes its own skill
    level; the card does not expose another member's progression; completing
    or undoing the card updates the displayed level after redirect.
  - Verify: Add Django view/template tests, then run the focused application
    suite.
  - Files: `src/dashboard/views.py`,
    `src/dashboard/templates/dashboard/preview.html`,
    `tests/application/test_dashboard.py`

- [x] Task 4: Add skill XP bar to selected-skill detail
  - Acceptance: Selected detail shows skill XP, next threshold or max-level
    state, and an accessible progressbar; the selected skill remains
    authorized by `request.user`; no account-level presentation regresses.
  - Verify: Extend application tests and run the focused browser workflow at
    existing repository viewport sizes.
  - Files: `src/dashboard/views.py`,
    `src/dashboard/templates/dashboard/preview.html`,
    `src/dashboard/static/dashboard/styles.css`,
    `tests/application/test_dashboard.py`,
    `tests/browser/test_skill_library_browser.py`

### Checkpoint: Dashboard behavior

- [x] Authenticated completion flow shows skill and account progression.
- [x] Undo reverses skill XP and account XP without double-awarding.
- [x] Cross-account isolation and archived-history behavior are covered.
- [x] Browser tests pass for landing-card level and selected-detail XP bar.

### Phase 3: Quality and handoff

- [x] Task 5: Verify complete feature and document the architectural boundary
  - Acceptance: The final implementation matches this spec, retains separate
    completion models, and documents any non-obvious service boundary.
  - Verify: Run `docker compose run --rm web pytest tests/application`,
    `docker compose run --rm web pytest tests/browser`,
    `docker compose run --rm web ruff format --check .`,
    `docker compose run --rm web ruff check .`, and `git diff --check`.
  - Files: `docs/decisions/` only if implementation adds a new decision;
    otherwise no additional documentation file is required.

### Checkpoint: Complete

- [x] All success criteria in the approved spec pass.
- [x] Final diff contains no secrets, generated reports, or local volumes.
- [x] The branch is ready for code review.

## Risks and Mitigations

| Risk | Impact | Mitigation |
|---|---|---|
| The two domains use different skill identifiers and completion tables. | High | Pass authorized model instances into separate domain adapters behind one value-object API; never infer the source from an integer ID. |
| Skill level semantics drift from account level semantics. | Medium | Reuse `level_threshold`, `level_for_xp`, and percentage logic; add shared threshold/cap tests for both scopes. |
| Archived private history disappears from derived totals. | High | Query historical completions independently of active selection state and add an archive regression test. |
| Dashboard query changes cause N+1 progression queries. | Medium | Build counts in the dashboard context deliberately and inspect query behavior during tests; optimize only if the existing data shape requires it. |
| UI labels confuse account level and skill level. | Medium | Use explicit “Account level” and “Skill level” labels and accessible progressbar names. |

## Open Questions

None. Phase 2 is based on the approved answers recorded in the spec.

## Implementation Gate

The human must review and approve this plan before Phase 3 task execution.
