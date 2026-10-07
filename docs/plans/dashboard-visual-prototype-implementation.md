# Implementation Plan: Dashboard Visual Prototype

> Historical — authentication portions superseded by
> [Internal Team Accounts](../specs/internal-team-accounts.md).

## Overview

Replace the client-only dashboard preview with an approved, fixed-demo
server-side sign-in and signed session, without adding a data model.

## Tasks

1. Specify failing server-side tests for valid, invalid, persistent, and logout
   flows.
   - Acceptance: the current client-only preview cannot satisfy the tests.
   - Verify: focused pytest fails before the new views exist.
2. Add configuration-backed POST sign-in/logout handlers and signed-cookie
   session configuration.
   - Acceptance: only configured values sign in; session state contains no
     credentials; logout clears access.
   - Verify: focused pytest.
3. Render either a CSRF-protected sign-in form or the dashboard based on the
   verified session; remove the client-only login path.
   - Acceptance: unauthenticated visitors cannot view dashboard content;
     desktop dashboard retains filler skill and streak-history displays.
   - Verify: full pytest, coverage, Ruff, and browser verification when
     available.

## Risks

| Risk | Mitigation |
| --- | --- |
| Demo password committed | Require runtime environment configuration and keep `.env` untracked. |
| Credential probing | Return one generic failure response and use constant-time comparison. |
| Session tampering | Use Django's signed HTTP-only cookie session with CSRF-protected forms. |
| Wireframe pages accidentally expanded | Do not add routes or actions beyond sign-in, dashboard, and logout. |
