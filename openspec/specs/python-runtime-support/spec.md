# python-runtime-support Specification

## Purpose
Define evidence-based CPython support promotion, installed-extra compatibility and unchanged safety guarantees across supported interpreters.

## Requirements

### Requirement: Evidence-based CPython 3.15 support

The project SHALL announce standard CPython 3.15 support only after verifying
its stable release status and passing full-suite and isolated installed-wheel
checks on that interpreter. Existing CPython 3.11–3.14 support SHALL remain.
An open requires-python range SHALL NOT be treated as verified support.

#### Scenario: Available 3.15 interpreter is prerelease

- **GIVEN** an official 3.15 prerelease interpreter
- **WHEN** compatibility is investigated
- **THEN** its probe is explicitly experimental and separate from required supported-version jobs
- **AND** neither passing nor failing the probe changes the stable support claim.

#### Scenario: Stable 3.15 passes compatibility gates

- **GIVEN** a stable 3.15 interpreter and reviewed compatible dependencies
- **WHEN** full quality, isolated wheel and latest-all jobs pass
- **THEN** 3.15 is added to blocking supported-version CI and documented classifiers/policies
- **AND** all previously supported interpreter jobs remain required and green.

### Requirement: Explicit dependency and extra compatibility

The system SHALL verify the base package, each documented extra and all extras
on CPython 3.15 from built artifacts in clean environments. Dependency changes
SHALL preserve the Python 3.11 baseline and document tested profiles, native
wheel availability and unresolved upstream blockers.

#### Scenario: A native extra has no compatible tested installation

- **GIVEN** an extra dependency cannot install or pass its contracts on 3.15
- **WHEN** compatibility evidence is evaluated
- **THEN** full 3.15 support remains unannounced and the blocker is recorded
- **AND** the extra is not silently removed, skipped or replaced by another runtime's evidence.

### Requirement: Interpreter upgrades retain safety and deterministic execution

CPython 3.15 SHALL preserve workspace boundaries, summary-only MCP responses,
source-free generation, exact-fingerprint approval, mandatory validation and
finite resource budgets. Repeated generation with the same recorded environment,
ordered spec and seed SHALL remain deterministic across supported worker/batch
settings. Cross-interpreter byte identity SHALL NOT be claimed without evidence.

#### Scenario: Spawn worker or MCP recovery fails on 3.15

- **GIVEN** a fictional dataset and a bounded generation or SDK stdio workflow
- **WHEN** cancellation, deadline expiry, tampering or interrupted recovery occurs
- **THEN** existing rejection, worker reaping and atomic cleanup contracts hold
- **AND** no validation, approval or resource guard is disabled to make compatibility checks pass.

### Requirement: Traceable compatibility promotion

Support promotion SHALL record the exact source revision, interpreter, platform,
dependency profiles and test outcomes. Alternative/free-threaded builds and new
platform support SHALL require separate evidence and SHALL NOT be implied by
standard CPython compatibility. Publication SHALL retain all applicable release
and review gates and require separate authorization.

#### Scenario: An experimental probe is green but release evidence is absent

- **GIVEN** only a successful experimental compatibility probe
- **WHEN** a release support claim is prepared
- **THEN** stable 3.15 support and release completion remain unchecked
- **AND** current supported-version and supply-chain gates remain enforced.
