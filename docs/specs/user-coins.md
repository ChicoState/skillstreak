# Spec: User Coins and Streak Rewards

## Objective

Add a permanent, user-owned coin currency for the first progression slice. Coins
are earned automatically from level-ups and streak milestones, recorded in an
auditable ledger, and shown as a current balance on the dashboard. Streak
milestones count completed scheduled occurrences so non-daily skills work fairly.

## Tech Stack

- Python 3.14, Django 5.2 LTS, PostgreSQL, pytest-django, and Playwright.
- Existing `skills` and `tracking` Django apps remain the completion sources.

## Success Criteria

- Coin awards are immutable, positive ledger entries with unique event keys.
- Reprocessing a completion or level-up never awards the same event twice.
- Individual skill streaks award demo-friendly configured milestones based on
  scheduled occurrences. Odd week milestones are one-time; even week
  milestones are repeatable after a streak reset.
- Overall highest streak rewards are one-time lifetime records and pay more than
  individual skill rewards.
- Level-up rewards are one-time per user and level.
- A reset never removes coins.
- Dashboard shows the current balance and both per-skill and overall next-reward
  amount/countdown projections.
- Demo tooling can grant coins without changing production reward rules.

## Boundaries

- Always: use transactions, unique event keys, account ownership checks, and
  tests before behavior changes.
- Ask first: catalog/purchase models, new dependencies, or changes to the
  approved infrastructure plan.
- Never: claw back earned coins, expose another user’s balance, or build the
  catalog and title purchasing flow in this PR.

## Out of Scope

Catalog design, titles, purchases, catalog administration, and user-facing
ledger history.
