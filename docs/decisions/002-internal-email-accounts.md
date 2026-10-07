# ADR-002: Use email-only internal team accounts

## Status

Accepted — 2026-10-05

Supersedes [ADR-001](001-fixed-demo-sign-in.md).

## Context

The fixed demo credential was appropriate for the first visual prototype but
cannot provide separate, durable accounts for the project team. The team needs
self-service registration and normal returning-user sign-in without adding an
outbound email provider or public-account lifecycle.

## Decision

Use a custom Django user model from the first project migration. Its normalized
`@csuchico.edu` email address is the unique login identifier; there is no
username. Store Django authentication sessions in PostgreSQL, retain the
existing fourteen-day session age, and use Django's built-in password validators
and password hashing.

Registration creates a usable account immediately. It verifies the domain only,
not mailbox ownership. Sign-in, duplicate registration, and redirect behavior
avoid disclosure beyond generic failure messages and the dashboard always
redirects unauthenticated visitors to the sign-in page.

## Consequences

- The custom user model must remain configured before the first applied shared
  migration; a database already migrated with `auth.User` requires a separately
  reviewed migration project.
- No email verification means email addresses are not trusted recovery or
  notification channels. Password reset/change, email change, invitations, and
  account deletion are intentionally deferred.
- The demo environment credentials and signed-cookie authorization marker are
  removed. Existing demo cookies cannot authorize the dashboard.
