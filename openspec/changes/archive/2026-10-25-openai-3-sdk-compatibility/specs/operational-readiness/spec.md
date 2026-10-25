# Operational Readiness Delta: openai-3-sdk-compatibility

## Added Requirements

### Requirement: Provider SDK Major Ranges Require Compatibility Evidence

The project SHALL expand a provider SDK major-version range only after an
identified release passes the provider-specific contracts, supported-runtime
matrix, and reviewed dependency compatibility gate.

#### Scenario: A range-only provider major update is proposed

- **GIVEN** package metadata expands the OpenAI SDK range from `<3.0.0` to
  `<4.0.0`
- **AND** the compatibility policy, reviewed lock, tests, or documentation still
  describe only OpenAI 2.x
- **WHEN** repository and release checks run
- **THEN** the change fails as unreviewed dependency range drift
- **AND** no supported-version claim or release artifact is published

#### Scenario: OpenAI SDK 3.x compatibility is declared

- **GIVEN** an identified stable OpenAI SDK 3.x release
- **WHEN** maintainers propose expanding the optional extra to `<4.0.0`
- **THEN** provider request, structured-response, timeout, error-redaction, and
  doctor contracts pass on every supported Python version
- **AND** `pyproject.toml`, the reviewed compatibility policy, `uv.lock`,
  compatibility documentation, and release notes agree on the support decision
- **AND** tests use synthetic metadata, fake transports, and no live credential
  or external provider request

#### Scenario: The evaluated major version breaks a provider boundary

- **GIVEN** the selected OpenAI SDK 3.x release violates an adapter, redaction,
  resource-bound, runtime, or review-gate contract
- **WHEN** compatibility evidence is reviewed
- **THEN** `<3.0.0` remains the declared upper bound
- **AND** the failure is reproduced by a focused local test before remediation
  or a separate compatibility change is proposed
