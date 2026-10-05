# ADR-003: Adopt the full schema while exposing a binary-only tracker UI

## Status

Accepted — implemented for the local MVP.

## Context

The approved SQL design supports system skills, per-user selections, daily
completions, schedules, and optional metrics. The immediate MVP needs only
selectable system skills and a yes/no daily action for each one.

## Decision

Represent every schema entity through Django models and migrations. Seed all
system skills from `initial_data.sql`, start demo accounts with Touch Grass
selected, and expose only binary selection/completion workflows. The richer
metric and schedule models remain without user-facing controls.

## Alternatives considered

- Build only `Skill`, `UserSkill`, and `DailyCompletion`: rejected because the
  user requested the complete approved SQL schema.
- Apply `schema.sql` directly: rejected because Django migrations are the
  repository's schema lifecycle and safely reference the configured user model.
- Expose metrics and schedules immediately: rejected because it expands the
  MVP past binary daily tracking.

## Consequences

The initial migration is larger, but future metric and schedule work starts
from a durable schema. The dashboard remains deliberately simple.
