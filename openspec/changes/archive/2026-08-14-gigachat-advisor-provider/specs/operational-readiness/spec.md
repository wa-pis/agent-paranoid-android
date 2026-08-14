# Operational Readiness Specification Delta

## Added Requirements

### Requirement: GigaChat Doctor Smoke Is Local

Doctor SHALL verify the optional GigaChat capability without credentials or an
external request.

#### Scenario: GigaChat capability is healthy

- **GIVEN** the GigaChat extra is required and importable
- **WHEN** doctor runs without `--skip-smoke`
- **THEN** it constructs and closes the adapter through an injected fake SDK
  client
- **AND** it validates strict structured-response parsing and advisor
  construction
- **AND** it does not read a real credential, obtain an access token, or use
  network access

#### Scenario: GigaChat capability fails

- **GIVEN** SDK import, adapter construction, parsing, or cleanup fails
- **WHEN** doctor reports the failure
- **THEN** doctor exits unsuccessfully with exact extra reinstall guidance
- **AND** exception text, credentials, tokens, paths, prompts, and responses
  are not exposed

### Requirement: GigaChat Extra Preserves The Supported Runtime Matrix

The GigaChat dependency profile SHALL pass the project's supported Python,
packaging, dependency, and license gates before release.

#### Scenario: Optional dependency profile is accepted

- **GIVEN** the proposed GigaChat SDK dependency range
- **WHEN** isolated package gates run on Python 3.11 through 3.14
- **THEN** base, `gigachat`, and `all` wheels build, install, import, and pass
  local doctor smokes
- **AND** minimum and latest accepted SDK versions pass fake-transport contract
  tests
- **AND** all transitive dependency licenses satisfy project policy

#### Scenario: SDK compatibility is incomplete

- **GIVEN** the SDK or a transitive dependency fails a supported interpreter,
  packaging, license, or bounded-adapter gate
- **WHEN** implementation readiness is evaluated
- **THEN** the provider extra is not merged or released
- **AND** the base support matrix is not narrowed silently
- **AND** a custom protocol implementation is not substituted without a
  revised reviewed OpenSpec

### Requirement: GigaChat Release Tests Are Externally Independent

Normal CI and release acceptance SHALL validate the GigaChat adapter with
synthetic inputs and fake transport only.

#### Scenario: Release gates exercise GigaChat

- **GIVEN** no GigaChat credential or network access is available
- **WHEN** unit, CLI, doctor, package, and isolated-wheel checks run
- **THEN** they cover successful and fail-closed adapter behavior with
  synthetic profiles
- **AND** no paid call or provider account is required
- **AND** no production data or private infrastructure context is used

#### Scenario: A maintainer performs an optional live smoke

- **GIVEN** an explicit test credential and a synthetic profile
- **WHEN** the separately gated manual smoke is authorized
- **THEN** the request remains metadata-only and review-gated
- **AND** credentials, request content, and response content are not printed or
  retained
- **AND** failure of an unavailable optional account is not represented as a
  deterministic-core regression
