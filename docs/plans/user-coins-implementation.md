# Implementation Plan: User Coins and Streak Rewards

## Architecture Decisions

- Add a focused `coins` Django app with an immutable ledger model. The current
  balance is derived from ledger entries, matching the existing derived XP
  approach while retaining auditability.
- Keep reward thresholds and amounts as explicit seeded constants for this PR;
  catalog and administrator reward configuration remain out of scope.
- Use unique event keys for level-up, individual-skill, and overall-record
  awards. Completion mutations call one transaction-safe award service.
- Calculate selected-skill streaks from completed scheduled occurrences, not
  calendar days, and build countdown metadata from the next eligible scheduled
  occurrence dates.

## Ordered Tasks

1. Add the coin ledger, reward constants, and unit/integration tests for balance
   and idempotent awards.
2. Add scheduled-occurrence streak calculations and tests for daily, weekly, and
   monthly schedules, including repeatable milestones.
3. Connect automatic awards to both completion mutation paths and level changes;
   add demo grant management command and tests.
4. Add dashboard balance and per-skill/overall reward countdown context and
   presentation, then verify the authenticated browser flow.

## Verification Checkpoints

- After task 1: coin model migrations and ledger tests pass.
- After task 2: recurrence/streak tests pass, including non-daily schedules.
- After task 3: existing progression and completion tests pass with no duplicate
  ledger entries.
- After task 4: dashboard tests, browser checks, formatting, and diff checks pass.
