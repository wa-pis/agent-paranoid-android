# Public Contracts Specification Delta

## Added Requirements

### Requirement: GigaChat Provider Selection Is Additive

The public advisor CLI SHALL add GigaChat without changing existing provider,
workspace, JSON, artifact, or deterministic-core behavior.

#### Scenario: User explicitly selects GigaChat

- **GIVEN** the optional GigaChat extra and runtime authentication are
  configured
- **WHEN** `agent-advise WORKSPACE --provider gigachat` runs
- **THEN** the existing workspace and advisor result contracts are used
- **AND** an optional bounded model override uses the existing model option
- **AND** the provider remains labelled experimental
- **AND** no new serialized credential or raw provider-response contract is
  introduced

#### Scenario: GigaChat extra is absent

- **GIVEN** the base package is installed without the GigaChat extra
- **WHEN** the user selects `--provider gigachat`
- **THEN** the command exits with stable installation guidance for
  `agent-paranoid-android[gigachat]`
- **AND** no SDK import traceback, credential value, provider response, or
  source literal is displayed

#### Scenario: Existing users do not select GigaChat

- **GIVEN** an existing CLI or Python workflow
- **WHEN** it runs after the additive provider release
- **THEN** command names, defaults, options, exit codes, JSON schemas, and
  artifacts remain compatible
- **AND** the deterministic advisor remains available without the GigaChat SDK

### Requirement: GigaChat Authentication Is Runtime Only

The public GigaChat contract SHALL keep authentication outside CLI arguments,
workspace artifacts, and provider-neutral models.

#### Scenario: User configures authorization-key mode

- **GIVEN** `GIGACHAT_CREDENTIALS` and one supported `GIGACHAT_SCOPE`
- **WHEN** the adapter initializes
- **THEN** the values are resolved only for that provider invocation
- **AND** the scope is validated against the three documented API scopes
- **AND** credentials and acquired tokens are not persisted or returned

#### Scenario: User configures access-token mode

- **GIVEN** `GIGACHAT_ACCESS_TOKEN` and no authorization key
- **WHEN** the adapter initializes
- **THEN** the token is used only in memory for that provider invocation
- **AND** conflicting authentication modes fail before network work
- **AND** no secret appears in settings, diagnostics, artifacts, or errors

### Requirement: GigaChat Endpoint Security Is Fixed

The public GigaChat integration SHALL use the official HTTPS service with
certificate verification enabled.

#### Scenario: A trusted local CA bundle is needed

- **GIVEN** an explicit readable `GIGACHAT_CA_BUNDLE_FILE`
- **WHEN** the SDK client is constructed
- **THEN** TLS verification remains enabled with that trust bundle
- **AND** the local path is not serialized or exposed in a public error

#### Scenario: Insecure or arbitrary routing is requested

- **GIVEN** configuration attempts to disable verification or replace the API
  or OAuth endpoint
- **WHEN** provider settings are validated
- **THEN** initialization fails before credentials or metadata leave the
  process
- **AND** no insecure fallback is attempted
