# Container Deployment Specification

## Purpose

Define optional, least-privilege OCI packaging for the CLI and MCP services
without weakening their existing trust boundaries.

## Requirements

### Requirement: Least-Privilege Container Targets

The project SHALL provide separate non-root container targets whose installed
dependencies match the CLI, generator MCP, and Trino MCP trust boundaries.

#### Scenario: Generator image is inspected

- **WHEN** the generator MCP image contract is checked
- **THEN** MCP and core generation dependencies are present
- **AND** Trino, SQLGlot, and PyArrow are absent
- **AND** the configured runtime user is not root

### Requirement: Isolated MCP Deployment

The recommended Compose deployment SHALL restrict filesystem, privilege,
resource, secret, and network access by service role.

#### Scenario: Generator and Trino services are deployed

- **WHEN** the Compose contract is inspected
- **THEN** both filesystems are read-only and all capabilities are dropped
- **AND** the generator has a bounded workspace but no network
- **AND** the Trino service has network access but no generator workspace
- **AND** each worker has a separate audit key and writable audit directory
- **AND** audit keys are mounted as secret files rather than environment text

### Requirement: Verifiable Container Publication

Release container images SHALL be multi-platform, content-addressed, and
verifiable without stored signing credentials.

#### Scenario: A version tag is pushed

- **WHEN** the container publication workflow succeeds
- **THEN** each target is published for amd64 and arm64
- **AND** BuildKit SBOM and provenance attestations are attached
- **AND** GitHub attests the published manifest digest
- **AND** Cosign signs the same digest with a short-lived GitHub OIDC identity

### Requirement: Shared Runtime OpenSSL Security Floor

All three final container targets SHALL inherit a shared runtime with Bookworm
libssl3 and openssl at least3.0.22-1~deb12u2. Targeted package installation and
version assertions SHALL fail closed. HIGH/CRITICAL vulnerability gates and
hardened workload checks SHALL remain enabled.

#### Scenario: Base image predates the OpenSSL correction

- **WHEN** a CLI, generator MCP or Trino MCP image is built
- **THEN** both fixed OpenSSL packages are installed in the shared runtime
- **AND** a missing fixed package or failed version assertion stops the build
- **AND** the normal scanner and workload checks must pass before merge
