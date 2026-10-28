# ADR-003: Derive account progression from completion history

## Status

Accepted — 2026-10-14.

## Context

The XP feature needs a private, account-level total and level. Members may undo
completions, including eligible dates during the prior week. Persisting a second
mutable XP balance or level value risks drift when a completion is retried,
deleted, or changed concurrently.

## Decision

Create a dedicated `skills` Django app that owns:

- `Skill`, owned by one account;
- a weekly weekday schedule for each skill; and
- one dated completion record per skill/date.

The account's XP is derived as the number of its completion records multiplied
by 10. Its level is derived from that XP with the approved cumulative threshold
formula, capped at level 99. The dashboard and mutation response use these
derived values; no denormalized XP or level balance is stored.

The account model stores the validated IANA timezone needed to convert a
browser's local date into the feature's calendar rules. A uniqueness constraint
on each `(skill, completed_on)` pair prevents duplicate XP awards at the data
layer. Completion mutations execute in a database transaction.

## Alternatives Considered

### Store XP and level on the account

- Pros: fast dashboard reads.
- Cons: a reversible completion needs coordinated updates and recovery from
  partial or concurrent writes; the stored values can diverge from history.
- Rejected: the first slice has a small data volume, making derived aggregates
  simpler and more trustworthy.

### Store an immutable XP-event ledger plus a current balance

- Pros: detailed audit trail and future support for multiple XP sources.
- Cons: adds ledger and reconciliation rules before any product need exists.
- Rejected: this slice has exactly one reversible XP source.

### Keep schedules and completions in `dashboard`

- Pros: fewer Django apps.
- Cons: mixes presentation with the product domain and makes future use outside
  the dashboard harder.
- Rejected: user-owned skills and progression form an independent domain.

## Consequences

- The feature requires a `skills` migration and a migration adding timezone to
  the custom account model.
- XP and level always reflect completion history and can be safely recomputed.
- Future XP sources need an intentional ADR revision rather than silently
  changing the calculation.
- Dashboard aggregate queries should be monitored if data volume later makes
  the derived calculation expensive.
