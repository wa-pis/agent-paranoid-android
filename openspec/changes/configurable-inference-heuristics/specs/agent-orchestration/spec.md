## ADDED Requirements

### Requirement: Configurable deterministic inference

Inference SHALL support a validated, versioned declarative configuration for
extending built-in heuristics with user rules and supported settings. The same
metadata and effective configuration SHALL produce equivalent proposals across
supported source adapters and Python, CLI and MCP, independently of export format.

#### Scenario: Domain-specific identifier rule

- **GIVEN** equivalent safe profiles and a rule matching a domain identifier name
- **WHEN** inference runs through different supported interfaces
- **THEN** it proposes the same typed field interpretation with rule provenance
- **AND** absent configuration preserves existing inference behavior
- **AND** missing metadata is reported rather than invented

### Requirement: Reviewable precedence and configuration identity

Explicit reviewed specification choices SHALL remain authoritative. User rules
SHALL precede built-in heuristic defaults; incompatible equal-priority proposals
SHALL require a diagnostic and review. Effective configuration SHALL be included
in inference evidence and cache/review identity without exposing sensitive values.

#### Scenario: Conflicting custom rules

- **GIVEN** two equal-priority rules propose incompatible field interpretations
- **WHEN** inference evaluates them
- **THEN** it reports the conflict without silently selecting a winner
- **AND** changing configuration invalidates stale inference and approval bindings

### Requirement: Custom heuristics preserve enforcement boundaries

Custom heuristics SHALL remain bounded inference proposals, subject to existing
deterministic validation, privacy, access, resource and approval controls. They
SHALL NOT execute arbitrary code or SQL, copy source rows, grant preservation
authority or replace generation business-rule enforcement.

#### Scenario: Unsafe or invalid customization

- **GIVEN** configuration requests unsupported executable behavior or exceeds limits
- **WHEN** configuration is loaded
- **THEN** it is rejected before inference with a redacted diagnostic
- **AND** no access, preservation or approval authority is granted
