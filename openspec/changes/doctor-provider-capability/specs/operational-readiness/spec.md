# Operational Readiness Delta

## Added Requirements

### Requirement: Provider Doctor Capability Smoke

Doctor SHALL verify the required provider capability with local SDK and
adapter construction, not importability alone.

#### Scenario: Provider capability is healthy

- **GIVEN** the OpenAI extra is required and importable
- **WHEN** doctor runs without `--skip-smoke`
- **THEN** it constructs and closes an SDK client with a non-secret placeholder
- **AND** it verifies structured response parsing and advisor construction
- **AND** no credentials, provider request, or external service is required

#### Scenario: Provider capability fails

- **GIVEN** SDK or adapter construction raises an exception
- **WHEN** doctor reports the failure
- **THEN** doctor exits unsuccessfully with exact extra reinstall guidance
- **AND** exception text, credentials, and sensitive data are not exposed
