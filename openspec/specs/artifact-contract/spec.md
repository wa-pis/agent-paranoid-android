# Artifact Contract Specification

## Purpose

Define compatibility and privacy guarantees for public generation bundle
artifacts and validation reports.

## Requirements

### Requirement: Generation Bundle Artifacts Are Stable

The package SHALL maintain reviewed contracts for generation bundle filenames
and the validation report.

#### Scenario: An artifact contract changes

- **GIVEN** the checked-in artifact layout and validation report fixtures
- **WHEN** an artifact is added, removed, renamed, or structurally changed
- **THEN** contract verification fails until compatibility is reviewed
- **AND** fixtures contain metadata only, not generated dataset rows
