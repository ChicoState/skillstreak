# Consolidated Email Reminders: Implementation Plan

### Problem to solve

Email reminders need a delivery path that is consolidated per user, respects
local preferences, and stays idempotent across retries and provider failures.

### Desired outcome

Deliver email reminders as a separate feature after in-app missed state exists.
The feature sends at most one eligible email per user at a time, supports digest
and simple modes, and never makes the email provider responsible for missed
state or schedule evaluation.

### Proposed solution

First add explicit email channel, content-mode, and local-time settings. Then
introduce a provider-neutral delivery service and durable attempt records.
Finally connect that service to a selected hosted provider and a scheduled job.
The job reads per-skill missed episodes, consolidates a user's due skills, and
uses the delivery record as its idempotency boundary.

### Alternatives considered

#### Reuse the dashboard request cycle to send email

Rejected. A browser request cannot guarantee delivery at the user's configured
local time and makes retries or inactive users unreliable.

#### Let the provider schedule and deduplicate reminders

Rejected. Provider-specific scheduling would hide domain decisions, make a
future provider change harder, and cannot reliably combine current skill state.

### Additional context

This plan implements [Consolidated Email Reminders](../specs/email-reminders.md).
It depends on the in-app missed-state slice and a chosen hosted email provider.
Password-reset self-service remains a separate follow-on issue after that
provider decision.

### Before submitting

- [ ] Do not begin provider integration until the provider and secret handling
      are approved.
- [ ] Verify every merge can run without live provider credentials.
- [ ] Verify delivery is disabled unless both global and email preferences allow it.
- [ ] Verify retries use durable idempotency, not process memory.

## Dependency graph

```text
profile master opt-in + timezone     in-app per-skill missed episodes
                 |                              |
                 v                              v
    email channel/mode/time preferences   due-skill consolidation
                 |                              |
                 +--------------+---------------+
                                v
                 delivery attempt / idempotency record
                                |
                                v
                  selected provider + scheduled execution
```

## Merge plan

### Merge 1: Email preferences and due-email policy

- Add email-channel, content-mode, and local reminder-time preferences to the
  existing Profile & settings surface.
- Preserve `reminders_enabled` as the master control; email remains off by
  default.
- Add a pure, tested policy that translates active missed episodes and the
  agreed escalation cadence into due skills for a user's local date/time.

**Done when:** a user can select in-app only, email only, or both; policy tests
cover the three-miss threshold, cadence, timezone, opt-out, completion, and
without sending an email.

### Merge 2: Provider-neutral, idempotent delivery

- Add a durable consolidated delivery-attempt model and database constraint for
  one user/email-date/escalation-step attempt.
- Add digest and simple message renderers with fake-provider tests.
- Ensure retryable failures can be retried and terminal outcomes are visible
  without exposing message contents or credentials.

**Done when:** concurrent/retried service tests prove one eligible email is
submitted at most once and content modes render correctly with a fake provider.

### Merge 3: Hosted provider and scheduled execution

- Select the provider, document environment variables and provider limits, and
  implement the narrow provider adapter.
- Add an authenticated/scheduled execution mechanism appropriate to the
  selected host; it must call the delivery service rather than embedding policy.
- Add sandbox verification and operational visibility for delivery failures.

**Done when:** provider sandbox delivery proves one consolidated email reaches
an opted-in account at the expected local time; failures are observable and
safe to retry.

## Risks and mitigations

| Risk | Mitigation |
| --- | --- |
| Duplicate email from retries or concurrent jobs | Database-enforced delivery idempotency plus transactional claiming. |
| Wrong local delivery time across DST | Compute due times from IANA timezone-aware values and test DST boundaries. |
| Provider outage loses reminders | Retain retryable attempts and expose failed delivery state for operations. |
| Email preference accidentally overrides the global opt-out | Require the master preference in every due-email query and test its transition. |
| Provider choice leaks into domain logic | Keep provider-specific code behind a small adapter used only by delivery. |
