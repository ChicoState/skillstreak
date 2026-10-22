# Spec: Dashboard Visual Prototype

## Status

Superseded for authentication by
[Internal Team Accounts](internal-team-accounts.md). The static dashboard
visual scope remains current.

## Objective

Provide the first browser-visible SkillStreak experience based on the supplied
wireframe. Visitors must pass a fixed demo sign-in to view a desktop-first,
responsive dashboard with illustrative skill data and streak history.

## Scope

- A server-rendered home page at `/`.
- An authenticated project-team session supplied by the internal-account flow.
- A desktop sidebar, dashboard header, skill summaries, and calendar-like
  streak-history display inspired by the wireframe.
- A predefined, filler skill library represented by static example entries.
- Desktop-first responsive layouts; narrow layouts remain supported but are
  not the MVP optimization target.

## Out of Scope

- Password recovery, user-owned dashboard data, database-backed skills, and API
  endpoints.
- Skill detail, add-skill, social, friends, chat, settings, and messages pages.
- Any claim that the illustrative progress data belongs to a real user.

## Commands

```sh
docker build --target runtime --tag skillstreak-dashboard-test .
docker run --rm --volume "$PWD:/app" --workdir /app skillstreak-dashboard-test pytest
docker run --rm --volume "$PWD:/app" --workdir /app skillstreak-dashboard-test ruff format --check .
docker run --rm --volume "$PWD:/app" --workdir /app skillstreak-dashboard-test ruff check .
```

## Structure

`dashboard` is a small Django app responsible for the server-rendered MVP.
Its template and CSS are colocated in the app. Access is controlled by Django
authentication; illustrative dashboard values remain static example entries.

## Testing Strategy

Focused Django client tests verify authenticated dashboard access, logout, and
dashboard content. Account-flow tests cover registration and sign-in. Browser
testing will verify the desktop interaction and layout when a browser-control
service is available.

## Boundaries

- Always: use CSRF-protected POST forms, generic failure messages, secure
  HTTP-only SameSite cookies, semantic HTML, and keyboard-operable controls.
- Ask first: add user-owned data, password recovery, email verification, or
  outbound email.
- Never: log submitted passwords or expose whether either sign-in field was
  individually correct.

## Success Criteria

- `/` redirects to sign-in when no authenticated session exists.
- Invalid sign-in attempts remain blocked with one generic error message.
- An authenticated account reaches the dashboard and remains signed in for up
  to 14 days; a POST logout clears the session immediately.
- The dashboard presents filler Jogging and Reading streak history on desktop;
  narrow layouts remain usable.
