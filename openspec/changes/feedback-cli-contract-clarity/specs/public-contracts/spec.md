## ADDED Requirements

### Requirement: Actionable Generation Mode Recovery

An incompatible generation mode/invalid-ratio combination SHALL explain both
safe recovery paths without changing CLI exit codes or publication semantics.

#### Scenario: A valid mode requests a nonzero invalid share
- **GIVEN** valid, edge or load_test and a nonzero invalid ratio
- **WHEN** a generation workflow validates the options
- **THEN** it explains that the selected mode rejects the ratio
- **AND** it offers omitting --invalid-ratio or choosing mixed/negative
- **AND** CLI exits 2 without publishing output or changing the input spec

#### Scenario: A zero ratio is supplied for valid generation
- **WHEN** valid, edge or load_test is selected with ratio zero
- **THEN** the combination remains accepted under its existing semantics
