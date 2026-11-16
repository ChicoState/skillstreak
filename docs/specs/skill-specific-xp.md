# Spec: Skill-Specific XP

## Status

Phase 1 approved — 2026-11-16. This document is the source of truth for the
implementation plan and feature work.

## Objective

Give an authenticated SkillStreak member a trustworthy XP total for each
skill, alongside the existing account-wide XP and level. A member should be
able to understand how much progress came from each selected or owned skill,
while the existing account progression continues to summarize all of the
member's eligible completions.

The first slice succeeds when skill-specific XP is derived from completion
history, remains consistent with account XP, is isolated to the signed-in
member, and is visible in the relevant dashboard skill presentation.

### Assumptions

1. Account XP remains the sum of all eligible completion records and continues
   to determine the account level.
2. Skill XP is derived from that skill's completion history rather than stored
   as a mutable balance.
3. The feature covers both account-owned skills and selected system skills.
4. Each eligible completion continues to award exactly 10 XP.
5. Undoing a completion removes its 10 XP from both the skill and account
   totals.
6. Leaderboards, sharing, badges, achievements, public progression, and new
   XP sources remain outside this slice.

## Tech Stack

- Python 3.14
- Django 5.2 LTS
- PostgreSQL through the existing Docker Compose development environment
- pytest and pytest-django for application tests
- Playwright/Chromium for browser verification
- Ruff for formatting and linting

No new dependency is expected.

## Commands

Run the focused application tests:

```sh
docker compose run --rm web pytest tests/application/test_progression.py tests/application/test_dashboard.py
```

Run the broader application suite:

```sh
docker compose run --rm web pytest tests/application
```

Run browser verification:

```sh
docker compose run --rm web pytest tests/browser
```

Check formatting and linting:

```sh
docker compose run --rm web ruff format --check .
docker compose run --rm web ruff check .
```

Check the final patch:

```sh
git diff --check
```

## Project Structure

- `src/skills/` — account-owned skill models and account-level progression
- `src/tracking/` — system-skill catalog, selected skills, and daily
  completions
- `src/dashboard/` — authenticated dashboard orchestration and presentation
- `tests/application/` — domain, authorization, view, and progression tests
- `tests/browser/` — Chromium dashboard behavior tests
- `docs/specs/` — reviewed product specifications
- `docs/plans/` — implementation plans created after this spec is approved
- `docs/decisions/` — architectural decisions when the implementation changes
  an established boundary

The implementation must preserve the current split between the legacy
account-owned `skills` domain and the selected-skill `tracking` domain unless
the approved plan explicitly chooses a consolidation.

## Code Style

Progression values should remain immutable, derived, and explicit. A likely
shape is a small value object or service result rather than a new stored XP
column:

```python
@dataclass(frozen=True)
class SkillProgression:
    skill_id: int
    total_xp: int
    completion_count: int


def progression_for_skill(user, skill_id: int) -> SkillProgression:
    """Derive one member's XP for one authorized skill."""
```

Use type annotations, short domain docstrings, Django querysets filtered by
the authenticated owner, and existing naming/formatting conventions. Do not
accept account or owner identifiers from submitted browser fields.

## Testing Strategy

### Domain tests

- A skill with no completions reports zero XP.
- Each completion contributes exactly 10 XP to its skill.
- Multiple completions for one skill accumulate without affecting another
  skill's total.
- Undoing a completion reduces the skill total by exactly 10 XP.
- Duplicate completion records remain impossible through existing constraints
  and mutation behavior.
- Account XP equals the sum of the member's skill-specific XP values across
  both completion domains.
- Existing level thresholds and the level-99 cap remain unchanged.

### Integration and authorization tests

- The dashboard exposes skill-specific XP for the signed-in member's visible
  skills.
- A member cannot retrieve or mutate another member's skill XP by changing a
  URL, query parameter, or submitted identifier.
- Empty, inactive, and unselected skills follow the approved display rules.
- Existing completion, undo, schedule, and reminder behavior remains intact.

### Browser tests

Verify the primary authenticated flow at the repository's existing responsive
browser sizes: select or create a skill, complete it, observe skill XP and
account XP, undo it, and observe both values reverse. Include at least one
cross-account visibility check if the UI exposes a skill identifier.

The existing project coverage floor and CI checks remain the minimum quality
bar; no dependency or CI change is part of this specification.

## Boundaries

- **Always:** derive XP from completion history; preserve account ownership
  filtering; keep account-level progression correct; add regression tests
  before changing behavior; run focused tests and `git diff --check`.
- **Ask first:** changing the XP award amount; adding configurable XP values;
  storing denormalized XP; changing level thresholds; merging `skills` and
  `tracking`; adding migrations that alter existing completion semantics;
  changing dependencies, CI, or infrastructure.
- **Never:** trust a browser-supplied owner/account identifier; expose another
  member's skill XP; award XP for duplicate, unscheduled, inactive, or
  unauthorized completions; add social/leaderboard behavior; commit secrets,
  generated artifacts, or local database volumes.

## Success Criteria

- Each authorized skill has a deterministic XP value equal to 10 times its
  eligible completion count.
- The account total equals the sum of its skill-specific XP values and remains
  the source for the existing level calculation.
- Completing and undoing a skill updates both the skill-specific and account
  totals without double-awarding XP.
- The dashboard displays the approved skill-specific XP value for the signed-in
  member's skills.
- Cross-account tests prove that skill XP cannot be read or changed through
  altered request parameters or URLs.
- Existing progression thresholds, level cap, schedules, reminders, and
  selected-skill behavior continue to pass.
- Focused application tests, browser tests, formatting, linting, and
  `git diff --check` pass before implementation is considered complete.

## Open Questions

1. Skill XP presentation: show a skill level indicator on dashboard cards and
   show the skill XP bar in the selected-skill detail view.
2. Inactive and archived skills retain their historical XP and remain included
   in account totals; the first UI slice does not delete or rewrite that
   history.
3. Keep the two Django completion models separate behind a shared progression
   service; do not consolidate the schemas in this feature.
4. Fixed 10 XP per completion applies to system and private skills.
5. Skill-specific XP has a skill-specific level and progress bar, using the
   existing threshold formula and level-99 cap independently for each skill.

## Next Gate

Phase 1 is complete. Phase 2 is the approved implementation plan; Phase 3
task execution still requires review of that plan before product code changes
begin.
