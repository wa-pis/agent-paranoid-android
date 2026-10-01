# ADR-0018: Deploy separate least-privilege CLI and MCP images

- Status: Accepted — retrospective baseline.
- Recorded: 2026-09-29. This is the recording date, not an invented original approval date.
- Authority and implementation boundaries: see Evidence below and the [register conventions](index.md#status-and-authority).

## Context

Generator workspace access and database network access have different risk profiles. A single privileged all-integrations image would conflate them.

## Decision

Maintain separate CLI, generator-MCP and Trino-MCP targets with minimal dependency sets. Run non-root, read-only rootfs, dropped capabilities, no-new-privileges and resource limits. Generator MCP has workspace access without network; Trino MCP has network without the generator workspace. Stdio has no published HTTP port. Separate audit secrets/mounts.

Validate AMD64 and ARM64 images; publish only through accepted signed version tags with SBOM/provenance and digest signatures. Health checks are local, not database reachability tests.

## Alternatives and consequences

One all-extras networked worker is simpler operationally but widens authority. Containers are optional; PyPI remains the ordinary local install route. Current images omit PyArrow rather than claiming every optional capability.

## Evidence

Sources: [container operations](../operations/containers.md), [container specification](https://github.com/wa-pis/agent-paranoid-android/blob/637065966c12584e11c9b437c1e8b8f8d708c0df/openspec/specs/container-deployment/spec.md).
Executable anchors: [container tests](https://github.com/wa-pis/agent-paranoid-android/blob/637065966c12584e11c9b437c1e8b8f8d708c0df/tests/test_containers.py), [container workflow](https://github.com/wa-pis/agent-paranoid-android/blob/637065966c12584e11c9b437c1e8b8f8d708c0df/.github/workflows/containers.yml).

## Revisit when

A new mount, network exposure, capability or image dependency needs an explicit deployment-boundary review.

