# Agent Orchestration Specification Delta

## Added Requirements

### Requirement: Reference Agent Flow Is Runnable And Review Gated

The project SHALL provide an executable application-layer example covering the
complete advisor-assisted workflow without requiring a provider SDK.

#### Scenario: A user runs the reference flow

- **GIVEN** a supported source and a new workspace
- **WHEN** reference planning and advisor proposal complete
- **THEN** generation stops pending human review
- **AND** read-only status reports the exact current spec fingerprint
- **AND** approval rejects a different fingerprint before writing output
- **AND** successful approval generates and validates a synthetic dataset
- **AND** JSON responses contain metadata and artifact paths, not rows
