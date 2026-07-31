# Run In Containers

Container images are an optional deployment path for isolated CLI and MCP
workers. PyPI remains the normal installation path for local Python use.

## Published Images

| Image | Entrypoint | Installed surface |
| --- | --- | --- |
| `ghcr.io/wa-pis/agent-paranoid-android-cli` | `test-data-agent` | Core CSV and JSON workflows |
| `ghcr.io/wa-pis/agent-paranoid-android-generator-mcp` | `test-data-agent-mcp-generator` | Core plus MCP |
| `ghcr.io/wa-pis/agent-paranoid-android-trino-mcp` | `test-data-agent-mcp-trino` | Core, MCP, Trino, and SQLGlot |

Release tags publish `linux/amd64` and `linux/arm64` manifests. PyArrow is not
installed in these images. Use the PyPI `parquet` extra when Parquet output is
required.

Pull requests build and run every target on both architectures. ARM64 checks
use QEMU only as CI execution support; the resulting image still reports
`arm64` and must pass the same non-root, read-only, network-isolated health
contract as the native AMD64 validation.

## Build Locally

Build only the target you need:

```bash
docker build --target cli -t agent-paranoid-android:cli .
docker build --target generator-mcp -t agent-paranoid-android:generator-mcp .
docker build --target trino-mcp -t agent-paranoid-android:trino-mcp .
```

The Dockerfile uses digest-pinned Python and uv images, a frozen lockfile, and
separate dependency sets. Final images run as UID/GID `65532` by default.

## Prepare Compose

Create writable workspace and audit folders plus a private audit key file:

```bash
umask 077
mkdir -p workspace audit/generator audit/trino secrets
openssl rand -base64 32 > secrets/generator_audit_hmac_key
openssl rand -base64 32 > secrets/trino_audit_hmac_key
chmod 600 secrets/generator_audit_hmac_key secrets/trino_audit_hmac_key
export CONTAINER_UID="$(id -u)"
export CONTAINER_GID="$(id -g)"
```

`CONTAINER_UID` and `CONTAINER_GID` must remain non-zero. They let the
non-root process write to bind-mounted host folders on Linux. Never commit the
`secrets`, `audit`, or `workspace` folders.

Build the Compose targets from the current checkout:

```bash
docker compose build cli generator-mcp trino-mcp
docker compose run --rm cli doctor --skip-smoke
```

The Compose contract applies a read-only root filesystem, drops all
capabilities, enables `no-new-privileges`, limits CPU, memory, processes, and
temporary storage, and publishes no ports.

## Generator MCP

The generator receives only `/workspace` and `/audit`; it has no network:

```bash
docker compose run --rm -T generator-mcp
```

An MCP client can launch that command directly. Use an absolute Compose path:

```json
{
  "mcpServers": {
    "test-data-generator": {
      "command": "docker",
      "args": [
        "compose",
        "-f",
        "/absolute/path/agent-paranoid-android/compose.yaml",
        "run",
        "--rm",
        "-T",
        "generator-mcp"
      ]
    }
  }
}
```

The client receives MCP messages over stdio. There is intentionally no exposed
HTTP port.

## Trino MCP

Set an HTTPS endpoint and narrow allowlists before starting the Trino worker:

```bash
export TRINO_HOST=trino.example.internal
export TRINO_PORT=443
export TRINO_USER=test_data_agent
export TRINO_ALLOWED_CATALOGS=iceberg
export TRINO_ALLOWED_SCHEMAS=dev,staging
docker compose run --rm -T trino-mcp
```

Missing host or allowlists fail before the server starts. The Trino service has
network access but receives no generator workspace mount. The Compose example
does not enable unrestricted access, plain HTTP, or the optional raw-SQL tool.

## Audit Secret

Compose mounts separate generator and Trino audit keys below `/run/secrets`.
Keys are not stored in image metadata or process environment. The application
rejects a secret file that is empty, oversized, writable by another user,
linked, or configured together with `TEST_DATA_AGENT_AUDIT_HMAC_KEY`.

The services also use separate host directories and logs:
`audit/generator/generator.jsonl` and `audit/trino/trino.jsonl`. A compromise of
one worker therefore does not grant the key or writable log mount of the other.
Stop the corresponding writer before rotating either file. See
[MCP Audit Logging](audit-logging.md).

## Verify A Published Image

Use the immutable digest shown by GHCR rather than relying on a mutable tag:

```bash
IMAGE=ghcr.io/wa-pis/agent-paranoid-android-generator-mcp
DIGEST=sha256:replace-with-published-digest

cosign verify \
  --certificate-identity-regexp \
  '^https://github.com/wa-pis/agent-paranoid-android/.github/workflows/containers.yml@refs/tags/v[0-9].*$' \
  --certificate-oidc-issuer https://token.actions.githubusercontent.com \
  "${IMAGE}@${DIGEST}"

gh attestation verify "oci://${IMAGE}@${DIGEST}" \
  --repo wa-pis/agent-paranoid-android

docker buildx imagetools inspect "${IMAGE}@${DIGEST}" \
  --format '{{ json .SBOM }}'
```

The release workflow signs the multi-platform manifest digest with a
short-lived GitHub OIDC identity and publishes BuildKit SBOM and provenance
attestations. No Cosign private key is stored in the repository.

Pull-request CI also scans every native container target for fixable High and
Critical operating-system and Python-package vulnerabilities. A finding at
either severity blocks publication through the container validation gate.
Unfixed upstream findings remain visible in the scan output and must be
reviewed separately during release-candidate security review.

## Health Semantics

The image health command performs only local checks: non-root execution,
expected dependencies, workspace access, Trino safety configuration, and audit
configuration. It never connects to Trino or reads a dataset. Because MCP uses
stdio, container liveness is also represented by the MCP process itself.
