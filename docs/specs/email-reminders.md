# Consolidated Email Reminders

### Problem to solve

Users who opt in need a dependable email nudge when unresolved missed skill
work reaches the agreed escalation threshold. Sending one email per skill
would be noisy, and the application does not yet have a hosted email provider
or an auditable delivery path.

### Desired outcome

An opted-in user can choose email reminders in addition to, or instead of,
the in-app missed-skill indicator. On an eligible date, they receive at most
one email for all qualifying skills.

The user can choose either a digest that names the missed skills or a simple
message: “Hey, you forgot to do something today.” They can opt out of email
reminders at any time. Turning off the global reminder preference immediately
clears active reminder state and prevents future email delivery.

### Proposed solution

Build on the durable per-skill missed episodes from the in-app reminder slice.
Add email channel and content-mode preferences to Profile & settings, retaining
the existing global reminder opt-in as the master control. A user may have
in-app indicators, email reminders, or both; email is disabled by default.

Use the user’s IANA timezone and configurable reminder time (default 8:00 PM)
to select due emails. Evaluate escalation per unresolved skill, consolidate all
skills due for a user into one email, and persist a delivery record before or
as part of provider submission so retries cannot create duplicate messages.

After three consecutive missed scheduled periods, the existing escalation
cadence is email-specific: every other calendar day three times, weekly three
times, then one final reminder one month later. Completing the skill or
turning off the global reminder preference immediately makes it ineligible.

### Alternatives considered

#### Send one email for each missed skill

Rejected. A consolidated email is less noisy and lets one reminder represent
the user's overall missed work.

#### Make email opt-in imply in-app indicators

Rejected. Users must be able to choose in-app reminders, email reminders, or
both independently under the existing master opt-in.

#### Add a hosted provider before a delivery model

Rejected. The application needs durable eligibility and idempotent delivery
records before a provider can safely retry or report failures.

#### Include password-reset email in this feature

Rejected. Once a hosted email solution is selected, self-service password
reset is a separate authentication issue with its own security review.

### Additional context

This feature depends on the in-app per-skill missed-state issue, profile
settings, and the user-skill schedule evaluator. It needs a selected hosted
email provider and a background/scheduled execution mechanism; neither is
currently chosen.

It does not add a profile inbox, push or SMS delivery, mobile time slots,
custom skills, or password-reset flows.

### Before submitting

- [ ] Select and document a hosted email provider and its production secrets.
- [ ] Confirm the profile supports email-only, in-app-only, and combined
      reminder choices under the master opt-in.
- [ ] Confirm at most one email is attempted per user and eligible date.
- [ ] Confirm digest and simple modes contain the intended content only.
- [ ] Confirm opt-out and completion suppress future sends.
- [ ] Confirm retries and provider failures cannot duplicate an email.

## Data contract

Keep missed episodes per `UserSkill`; do not make one email record the source
of truth for missed state. Add profile preferences for email delivery, email
content mode, and local reminder time. Add a durable delivery/attempt record
keyed so only one consolidated email can be sent to a user for a given local
eligible date and escalation step.

Provider request IDs, outcomes, and retryable failure metadata must be retained
without persisting provider credentials or email-body secrets in application
data.

## Acceptance criteria

- Email delivery is disabled by default and respects the master reminder opt-in.
- A user can choose email only, in-app only, or both.
- A due user receives at most one consolidated email, even if several skills
  are eligible or a job is retried.
- Digest mode identifies qualifying skills; simple mode does not identify
  individual skills.
- The user's local timezone and configured reminder time determine when a due
  email is considered for delivery.
- Global opt-out and completion prevent future sends for the affected episode.
- Provider failures are observable and safely retryable without duplicate mail.

## Verification

```sh
docker compose up -d db
docker compose run --rm web python manage.py migrate
docker compose exec web pytest tests/application --cov --cov-branch --cov-fail-under=80 --cov-report=term-missing
docker compose exec web ruff format --check .
docker compose exec web ruff check .
```

Use PostgreSQL-backed tests for delivery idempotency and preference ownership,
service tests for local-time and escalation boundaries, provider-adapter tests
with a fake provider, and browser tests for the email channel and content-mode
controls. Run a provider sandbox test only after the provider is selected.
