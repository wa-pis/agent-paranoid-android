## ADDED Requirements

### Requirement: RC5 Acceptance Identity

The `1.6.0rc5` release SHALL retain the existing signed publication and
independent exact-commit acceptance requirements. Historical campaign evidence
SHALL keep its actual source and artifact identity and SHALL NOT be relabelled
as execution on a later RC5 commit. General release authorization SHALL NOT
substitute for human review of a particular dataset specification.

#### Scenario: RC5 is prepared from the accepted runtime campaign

- **GIVEN** earlier runtime checks and a newly versioned RC5 candidate
- **WHEN** release readiness is assessed
- **THEN** earlier runs identify their real SHA, environment and coverage limits
- **AND** independent review, full release gates and Ubuntu artifact hashes bind
  to the exact final RC5 main commit
- **AND** actual client and human specification-review evidence remains distinct
  from automated SDK checks

#### Scenario: A required RC5 acceptance step is unresolved

- **GIVEN** missing human acceptance, failed required gates or unverified hashes
- **WHEN** publication readiness is assessed
- **THEN** RC5 remains unpublished until the required step is resolved
- **AND** existing release tags and repository protections remain unchanged
