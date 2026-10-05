# Spec: Internal Team Accounts

## Status

Approved — 2026-10-05.

## Objective

Let SkillStreak project-team members create and use their own accounts. A
member registers with an email address at `@csuchico.edu` and a password, is
signed in immediately, and can later sign in and out using the same email and
password to reach the existing sample dashboard.

## Scope

- Email-only Django user accounts; no username field is collected or exposed.
- Self-service registration restricted to normalized `@csuchico.edu` email
  addresses.
- Django-managed password hashing and built-in password validators.
- Server-side database sessions, CSRF-protected registration/sign-in/sign-out,
  and an authenticated dashboard route.
- Case-insensitive email storage and lookup by trimming and Unicode-casefolding
  the supplied email before storage or authentication.

## Out of Scope

- Public registration, invitation workflows, email verification, outbound email,
  password reset/change, email changes, account deletion, and user-owned skill
  or progress data.
- Proof that the person registering controls the supplied email address. Domain
  restriction is an accepted internal-prototype boundary, not verification.

## Commands

```sh
docker compose up --build
docker compose exec web python manage.py migrate
docker compose exec web pytest
docker compose exec web ruff format --check .
docker compose exec web ruff check .
```

## Boundaries

- Always: validate form input on the server, use Django password hashing and
  validation, use CSRF-protected POST forms, and return generic invalid-login
  and duplicate-registration errors.
- Ask first: add an outbound-email provider, password recovery, user-data
  persistence, role management, invitations, or rate limiting.
- Never: commit credentials, log passwords, reveal which sign-in field failed,
  or redirect to an arbitrary caller-supplied URL.

## Success Criteria

- An anonymous visitor is redirected from `/` to `/sign-in`.
- A `@csuchico.edu` member can register, is signed in immediately, and reaches
  the sample dashboard.
- An outside-domain email, duplicate email, invalid password, mismatched
  password, or invalid sign-in never creates an authenticated session.
- A returning member can sign in and sign out using email and password.
- The session is server-side and the dashboard displays the signed-in email,
  not demo identity content.
