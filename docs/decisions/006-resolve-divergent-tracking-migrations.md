# 006: Bridge the conflicting local tracking migration histories

## Status

Accepted for the merge of the skill-library and missed-reminder branches.

## Context

Both branches independently created a `tracking` migration numbered `0006`.
The skill-library branch creates tag tables, while the reminder branch creates
missed-episode tables. Some local databases already contain both sets of tables
and the old reminder migration records.

## Decision

Keep the skill-library migration as `0006`, move reminder state to migrations
`0007` and `0008`, and use `SeparateDatabaseAndState` bridge operations. The
bridge creates a reminder table only when it is absent, while always advancing
Django's model state. The theme field follows as the regular `0009` migration.

## Consequences

Fresh databases receive all tables in a deterministic order. Existing local
databases that already have the reminder tables keep their data and gain the
new migration records without duplicate-table failures. The compatibility code
is intentionally limited to this one divergent local-MVP merge.
