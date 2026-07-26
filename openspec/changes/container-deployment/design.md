# Design: container-deployment

## Image Boundaries

One multi-stage Dockerfile produces three final targets:

- `cli` contains only core dependencies;
- `generator-mcp` adds MCP but excludes Trino, SQLGlot, and PyArrow;
- `trino-mcp` adds MCP, Trino, and SQLGlot but excludes PyArrow.

Every target runs as UID/GID 65532 and includes a non-networking health command
that checks the target dependency contract. The base Python and uv images are
selected by immutable multi-platform digests.

## Runtime Boundaries

The Compose example keeps root filesystems read-only, drops all Linux
capabilities, enables `no-new-privileges`, limits processes, CPU, memory, and
temporary storage, and publishes no ports. The CLI and generator use
`network_mode: none`. Only the generator receives the workspace mount; only the
Trino service joins the egress-capable network.

MCP uses stdio, so no synthetic HTTP health endpoint is added. Docker invokes
the local package health module instead. It validates installation, non-root
execution, target dependencies, workspace access, safe Trino configuration,
and audit configuration without connecting to Trino or reading dataset rows.

## Secret Handling

Compose mounts separate base64 audit HMAC keys through Docker secrets and gives
each MCP worker its own writable audit directory. The application
accepts `TEST_DATA_AGENT_AUDIT_HMAC_KEY_FILE`, opens it without following
symlinks, bounds its size, and rejects non-regular, hard-linked, or writable
secret files. The file and existing direct environment value are mutually
exclusive.

## Release Supply Chain

Pull requests build and run each target locally without registry permissions.
Version tags must pass the full release gate before publishing
`linux/amd64` and `linux/arm64` images. The workflow attaches BuildKit SBOM and
maximal provenance attestations, pushes to GHCR, adds a GitHub provenance
attestation, and signs the manifest digest with Cosign and GitHub OIDC.
Actions, base images, uv, and Cosign are version or digest pinned.
