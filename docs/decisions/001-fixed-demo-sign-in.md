# ADR-001: Use a fixed, environment-configured demo sign-in for the MVP

## Status

Accepted — 2026-09-30

## Context

The MVP needs a verifiable sign-in gate and remembered access, but does not yet
need registration, user persistence, password recovery, or product data.

## Decision

Accept one identity configured through `DEMO_LOGIN_EMAIL` and
`DEMO_LOGIN_PASSWORD`. Compare submitted values server-side, establish a
Django-signed session after success, and clear it through a CSRF-protected
POST logout. The cookie stores only the boolean authorization marker and has a
14-day maximum age.

## Alternatives considered

- Client-only preview: rejected because it cannot block incorrect attempts.
- A hard-coded credential: rejected because credentials must not enter source
  control.
- Django user records: deferred because it requires models, migrations, and
  account lifecycle decisions beyond this MVP slice.

## Consequences

The demo login is suitable for local MVP validation only. A later real-account
feature must replace it with Django's user authentication and a durable session
strategy.
