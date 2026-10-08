# ADR-002: Use Django users for two local demo accounts

## Status

Accepted — applies to the selectable binary-skill MVP and supersedes ADR-001.

## Context

The original one-credential sign-in cannot own independent completion history.
The next MVP needs two separately authenticated local accounts so each user can
track their own skill history.

## Decision

Provision exactly two local Django users from untracked environment credentials
through an idempotent development command. Authenticate with Django's built-in
authentication helpers and attach UserSkill and DailyCompletion rows to the
authenticated user.

## Alternatives considered

- Keep a shared completion history: rejected because it violates per-account
  ownership.
- Store an email string directly on completions: rejected because it bypasses
  Django authorization and would require an ownership migration later.
- Add general registration: deferred because two configured local accounts are
  sufficient for the MVP.

## Consequences

Local setup gains a required migration and demo-account provisioning step.
Later real-account work can retain the ownership model and replace only the
provisioning workflow.
