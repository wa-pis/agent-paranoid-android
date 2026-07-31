# Change Proposal: container-deployment

## Summary

Add optional hardened OCI images for the CLI, generator MCP server, and Trino
MCP server without replacing the existing PyPI installation path.

## Motivation

MCP deployments need reproducible process isolation and explicit filesystem,
network, credential, and dependency boundaries. A single broad image would
give the generator unnecessary Trino dependencies and would make it easier to
mount database credentials into the wrong service.

## Scope

In scope:

- separate minimal Docker targets for CLI, generator MCP, and Trino MCP;
- non-root, read-only Compose examples with bounded resources;
- file-mounted audit secrets and isolated generator networking;
- multi-platform GHCR publication from release tags;
- image SBOMs, provenance attestations, and keyless signatures;
- static and runtime container contract tests.

Out of scope:

- replacing PyPI or local virtual-environment installation;
- bundling Trino itself;
- exposing an HTTP management or health API;
- storing credentials in images, Compose files, or GitHub repository secrets;
- publishing images from pull requests or unversioned commits.

## Safety Impact

The generator image has no Trino client or SQL parser and runs without a
network in the recommended deployment. The Trino image has no generator
workspace mount. Each MCP service uses a separate mounted audit key file and
bounded append-only audit directory. Container publishing uses short-lived
GitHub OIDC identities and immutable image digests.

## Compatibility

The Python API, CLI commands, MCP tool contracts, and DatasetSpec schema remain
unchanged. `TEST_DATA_AGENT_AUDIT_HMAC_KEY_FILE` is an additive alternative to
the existing environment value; configuring both is rejected.
