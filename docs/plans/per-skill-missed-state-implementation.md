# In-App Per-Skill Missed State: Implementation Plan

### Problem to solve

Miss detection, the dashboard's per-skill indicator, and the profile's missed
skills digest need one reliable domain model rather than scattered UI logic.

### Desired outcome

Deliver per-skill missed state in small merges. The resulting domain service is
idempotent and user-timezone-aware, without adding email or background-delivery
infrastructure.

### Proposed solution

Build persistence and reconciliation first, then surface the indicator and
completion-driven state in the dashboard and a separately dismissible digest
in the profile.

### Alternatives considered

#### Add an email sender first

Rejected. The provider would have to infer missed-state logic itself, coupling
delivery to schedule evaluation and making in-app feedback impossible to test
independently.

#### Derive dashboard icons only at render time

Rejected. Explicit state is required for completion-driven icons, fresh opt-in
windows, and a later email feature to consume without recreating history.

#### Add a global recurring job in this slice

Rejected. A scheduler/hosted job is a separate delivery-infrastructure
decision. This slice exposes reconciliation that future jobs can call and may
reconcile the current user within existing authenticated interactions.

### Additional context

This plan implements [In-App Per-Skill Missed State](../specs/per-skill-missed-state.md).
It depends on profile settings and the user-skill schedule evaluator. It does
not implement email, reminder-time preferences, a persistent profile inbox, or
mobile time slots.

### Before submitting

- [ ] Run PostgreSQL migration and active-episode constraint tests.
- [ ] Test local-midnight boundaries, idempotency, and consecutive misses.
- [ ] Test completion, opt-out, and re-opt-in resets.
- [ ] Test dashboard authorization and CSRF.
- [ ] Test profile-digest dismissal and reappearance after a new missed skill.
- [ ] Confirm no email backend, network request, or recurring job is added.

## Dependency graph

```text
profile reminder opt-in + timezone     user-skill expected-date evaluator
                  |                              |
                  +--------------+---------------+
                                 v
             per-skill missed episode + reconciliation service
                                 |
                 +---------------+---------------+
                 v                               v
    dashboard missed icon/completion      profile missed-skills digest
                                              + dismissal marker
```

## Merge plan

### Merge 1: Missed-state persistence and reconciliation

- Add the missed-episode model and migration with a database-enforced single
  active episode per `UserSkill`.
- Add an idempotent reconciliation service that evaluates missed local dates,
  maintains consecutive misses, closes states for opted-out users, and records
  the episode's missed-state facts.
- Add service/model tests for opt-in boundaries, local midnight, completion,
  and consecutive-miss counting.

**Done when:** migration, model, and service tests pass without dashboard,
email, or background-job changes.

### Merge 2: Dashboard missed indicator and completion

- Reconcile the signed-in user's active skills through the domain boundary.
- Render an accessible missed icon on each active skill with an active episode.
- Ensure normal completion also closes the relevant active episode.

**Done when:** view tests prove current-user ownership and state transitions;
a browser check shows an icon, completes its skill, and confirms it disappears.

### Merge 3: Profile digest and dismissal

- Render a profile-level digest of every active missed skill.
- Add a CSRF-protected, owner-only dismissal action that changes only the
  digest's visibility.
- Keep dashboard icons visible after digest dismissal.
- Update a visible digest as its listed skills are completed; remove it when no
  missed skills remain.
- Make the digest visible again when a later missed episode begins, with all
  active missed skills in its content.

**Done when:** view and browser tests prove dismissal does not affect icons,
the digest updates after completion, remains hidden without a new missed
episode, and a new missed skill makes it reappear.

## Risks and mitigations

| Risk | Mitigation |
| --- | --- |
| Multiple requests create duplicate active state | Use a database uniqueness guarantee plus transactional reconciliation. |
| Timezone/DST mistakes create early misses | Test dates in non-UTC IANA zones and derive boundaries from local calendar dates. |
| Dashboard GET mutations grow into hidden job behavior | Keep reconciliation a named, testable service and restrict it to the signed-in user's state; introduce global scheduling separately. |
| Dismissing a digest clears missed work | Store dismissal separately from skill episodes and test that icons remain. |
