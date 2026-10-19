# Spec: Private Custom Skill Goals

## Objective

Let a signed-in member add a private skill from the dashboard and choose the
kind of streak they want: daily, any N days per week, or any N days per
calendar month. The dashboard must show that skill's current goal progress.

## Scope

- A single Add skill link appears in the top-right of the dashboard overview.
- `/skills/new/` is a login-protected server-rendered form inspired by Figure B.
- Valid form submission atomically creates a private `Skill`, active
  `UserSkill`, and current `UserSkillSchedule` owned by `request.user`.
- Daily goals need no target. Weekly targets range from 1 to 7. Monthly targets
  range from 1 to 31 and count any completed calendar days in the month.
- The existing binary completion control remains the way to record activity.

## Boundaries

- Always: derive ownership from the session, validate POST data server-side,
  protect writes with CSRF, and escape custom name/description output.
- Never: accept creator, visibility, slug, or another user's identifiers from
  the form; expose private skills through the system skill library.
- Out of scope: custom-skill editing/deletion, public sharing, fixed weekdays
  or month dates, metrics, historical backfilling, and notifications.

## Success Criteria

- A member can create daily, weekly, and monthly custom goals.
- Another member cannot see or gain a selection for that private skill.
- Current cards show goal-aware text such as `3 of 4 days this week`.
- Existing system-skill selection and daily completion behavior stays intact.
