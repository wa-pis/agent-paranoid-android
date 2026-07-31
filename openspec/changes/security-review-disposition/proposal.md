# Change: security-review-disposition

## Why

Automated vulnerability, license, secret, code, and image gates are active, but
the remaining Scorecard findings need explicit evidence and risk ownership
before the operational-readiness review can close.

## What Changes

- Record a dated security baseline tied to a reviewed main commit.
- Separate code/runtime findings from Scorecard governance heuristics.
- Give every accepted or deferred finding an owner and revisit trigger.
- Keep the release-candidate audit as a separate mandatory gate.

## Impact

Maintainers gain an auditable review artifact. Runtime behavior, repository
settings, and public interfaces remain unchanged.
