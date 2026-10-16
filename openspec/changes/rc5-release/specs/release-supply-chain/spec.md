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

#### Scenario: A prepared manual plan is resumed

- **GIVEN** an actual client created a plan and the final specification was prepared afterward
- **WHEN** the human resumes that existing client conversation
- **THEN** the existing plan is inspected without replaying planning or deleting its workspace
- **AND** the full current specification is made available for human review before new specific consent
- **AND** consent predating that specification, resume preflight and automated checks do not close manual acceptance
- **AND** approval, validation, artifact verification and actual client completion remain separately evidenced
