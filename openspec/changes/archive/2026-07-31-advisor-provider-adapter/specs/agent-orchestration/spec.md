# Agent Orchestration Specification Delta

## Added Requirements

### Requirement: Advisor Client Adapter Preserves Trust Boundaries

The agent workflow SHALL adapt application-owned structured-output clients
without giving them authority over validation, approval, or generation.

#### Scenario: An in-process provider client returns a proposal

- **GIVEN** a safe fingerprint-bound advisor request
- **WHEN** the exchange adapter invokes the client
- **THEN** the client receives a defensive copy of trusted instructions,
  untrusted request metadata, and response schema
- **AND** its response is validated against the original request
- **AND** client mutation cannot weaken the validation source
- **AND** no persistence, approval, or generation occurs
