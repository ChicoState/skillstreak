# Spec: Dashboard Visual Prototype

## Status

Approved — the MVP uses a fixed, environment-configured demo sign-in with a
server-side session. It is not an account-registration or password-management
feature.

## Objective

Provide the first browser-visible SkillStreak experience based on the supplied
wireframe. Visitors must pass a fixed demo sign-in to view a desktop-first,
responsive dashboard with illustrative skill data and streak history.

## Scope

- A server-rendered home page at `/`.
- A POST-only sign-in form that accepts exactly one fixed demo identity from
  `DEMO_LOGIN_EMAIL` and `DEMO_LOGIN_PASSWORD` environment variables.
- A signed, HTTP-only Django session that persists the verified state across
  page loads for up to 14 days, or until the visitor logs out.
- A desktop sidebar, dashboard header, skill summaries, and calendar-like
  streak-history display inspired by the wireframe.
- A predefined, filler skill library represented by static example entries.
- Desktop-first responsive layouts; narrow layouts remain supported but are
  not the MVP optimization target.

## Out of Scope

- Django accounts, registration, password recovery, user models, migrations,
  database reads/writes, and API endpoints.
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
Its template and CSS are colocated in the app. It compares form values against
runtime configuration with a constant-time comparison and stores only a
boolean demo-session marker in Django's signed-cookie session backend.

## Testing Strategy

Focused Django client tests verify successful sign-in, failed sign-in, session
persistence, logout, and dashboard content. Browser testing will verify the
desktop interaction and layout when a browser-control service is available.

## Boundaries

- Always: use CSRF-protected POST forms, generic failure messages, signed
  HTTP-only SameSite cookies, semantic HTML, and keyboard-operable controls.
- Ask first: add real accounts, database persistence, dependencies, or a
  production demo-login policy.
- Never: commit the demo credential, log submitted values, or expose whether
  either login field was individually correct.

## Success Criteria

- `/` returns a sign-in prompt when no valid demo session exists.
- Invalid sign-in attempts remain blocked with one generic error message.
- A successful sign-in reaches the dashboard and remains signed in for up to
  14 days; a POST logout clears the session immediately.
- The dashboard presents filler Jogging and Reading streak history on desktop;
  narrow layouts remain usable.
