# 005: Persist a small set of user-selected color palettes

## Status

Accepted for the local MVP.

## Decision

Store a `theme` choice on each user's existing `UserPreference` record. The
supported values are Green (the existing default), Blue, and Purple. Server
rendered pages apply the value through a `data-theme` attribute, and the
dashboard stylesheet maps each palette through the existing semantic CSS
variables.

## Consequences

- The selection persists across sessions and devices with the user's account.
- A fixed Django choice field validates the submitted value; users cannot
  supply arbitrary CSS or theme names.
- New palettes are an additive model choice and CSS-variable definition, not a
  dashboard-layout rewrite.
