# Change Proposal: configurable-inference-heuristics

## Summary

Planned future capability: extend the built-in inference heuristics with user
rules and settings. This proposal does not implement a configuration surface
or promise a release date.

Users should be able to tune semantic field classification, candidate
relationships and inferred constraints using bounded declarative rules over
schema identifiers and safe profile metadata. Examples include recognizing a
company-specific identifier suffix or changing the confidence threshold for a
relationship candidate.

## Motivation

Built-in naming and metadata heuristics cannot cover every domain. Users need
repeatable domain knowledge without editing the application or depending on an
AI provider.

## Scope

In scope:

- A versioned, validated configuration for enabling/disabling built-in rules,
  supported thresholds, user matchers and typed inference proposals.
- Explicit precedence: safety constraints first; explicit reviewed specification
  choices remain authoritative; user rules precede built-in heuristic defaults.
  Equal-priority incompatible proposals require a diagnostic and review.
- Shared deterministic inference across supported sources and Python, CLI and
  MCP; equivalent metadata and settings produce equivalent proposals regardless
  of output format. Missing source metadata is reported, never fabricated.
- Rule identifiers, confidence, safe evidence and configuration fingerprints in
  review artifacts; cache identity includes the effective configuration.
- Documented configuration examples and a cross-interface acceptance matrix.

Out of scope:

- Arbitrary Python, shell, SQL or dynamically loaded executable plugins.
- Replacing dataset business rules: these rules propose a DatasetSpec; existing
  generation and validation enforce the reviewed specification and business rules.
- New source adapters, output formats or provider dependencies.

## Safety Impact

Rules use identifiers and safe metadata, never raw source rows or secret values.
Configuration size and evaluation work are bounded. Invalid rules fail before
inference and produce redacted diagnostics. Custom rules cannot relax privacy,
read-only access, allowlists, budgets, review, or local approval requirements;
classification cannot establish anonymization or authorize source preservation.
No new filesystem or database authority is granted.

## Compatibility

Omitting configuration preserves existing behavior. Exact syntax, supported
settings, configuration discovery and adapter arguments must be specified and
reviewed before implementation. Existing DatasetSpec semantics remain intact;
configuration changes invalidate stale inference evidence and approval bindings.
