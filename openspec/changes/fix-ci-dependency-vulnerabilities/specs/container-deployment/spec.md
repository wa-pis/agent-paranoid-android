## ADDED Requirements

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
