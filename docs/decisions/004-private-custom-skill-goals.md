# ADR-004: Store custom goals as private skills with count-based schedules

## Status

Accepted

## Context

Members need personal skills with daily, weekly, or monthly streak goals. The
existing relational model already represents private skills and daily/weekly
scheduling, but only supports fixed month dates rather than an any-N-days
monthly target.

## Decision

Create custom skills as `PRIVATE` records owned by the authenticated member and
immediately create their active `UserSkill`. Add a `DAYS_PER_MONTH` schedule
rule with a constrained `target_days_per_month` field. Goal progress is derived
from binary daily completions for the current UTC day, week, or calendar month.

## Consequences

The dashboard can represent user-selected streak goals without a second custom
skill model or a duplicate completion mechanism. The schedule constraint and
its Django migration must evolve together whenever additional recurrence types
are added.
