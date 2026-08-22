# Agent Paranoid Android

[![PyPI](https://img.shields.io/pypi/v/agent-paranoid-android.svg)](https://pypi.org/project/agent-paranoid-android/) [![CI](https://github.com/wa-pis/agent-paranoid-android/actions/workflows/ci.yml/badge.svg)](https://github.com/wa-pis/agent-paranoid-android/actions/workflows/ci.yml) [![Documentation](https://img.shields.io/badge/docs-GitHub%20Pages-blue.svg)](https://wa-pis.github.io/agent-paranoid-android/) [![OpenSSF Scorecard](https://api.scorecard.dev/projects/github.com/wa-pis/agent-paranoid-android/badge)](https://scorecard.dev/viewer/?uri=github.com/wa-pis/agent-paranoid-android) [![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

Deterministic synthetic test data from CSV and database metadata, without
copying source rows. Use the CLI or Python library to profile structure, review
a `DatasetSpec`, generate reproducible datasets, and validate the result.

Stable `1.3.0` is the recommended release. Read the
[documentation](https://wa-pis.github.io/agent-paranoid-android/) for complete
workflows and configuration.

Preview `1.3.1rc2` is explicit opt-in:
`python3 -m pip install "agent-paranoid-android==1.3.1rc2"`.

## Install And Try It

Python 3.11 or newer is required.

```bash
python3 -m pip install "agent-paranoid-android==1.3.0"
test-data-agent demo --output out/demo
```

The offline demo uses a bundled fictional fixture and needs no checkout,
network, database, or AI provider. A successful run reports:

```text
Generated synthetic dataset: out/demo | rows: customers=12 | seed: 20260801 | validation: passed | source rows copied: no
```

The output contains synthetic CSV data, a safe profile, the effective
`DatasetSpec`, a validation report, and a generation manifest. The demo has no
relationship or business-rule evidence, so it makes no claim about preserving
those properties.

## Start With Your Data

| Source | Start here |
| --- | --- |
| One CSV file | [First CSV Dataset](https://wa-pis.github.io/agent-paranoid-android/getting-started/first-csv/) |
| PostgreSQL | [PostgreSQL Workflow](https://wa-pis.github.io/agent-paranoid-android/how-to/postgresql/) |
| Trino | [Trino Workflow](https://wa-pis.github.io/agent-paranoid-android/how-to/trino/) |
| Existing `DatasetSpec` | [Profiles And Specs](https://wa-pis.github.io/agent-paranoid-android/concepts/profiles-and-specs/) |

CSV and JSON workflows are included in the base package. Install optional
database, Parquet, MCP, or AI support only when you need it; see
[Installation](https://wa-pis.github.io/agent-paranoid-android/getting-started/installation/).

## Guarantees And Limits

- An explicit seed makes generation reproducible under the recorded package,
  dependency, locale, and serializer environment.
- Source rows are never copied into generated output. Exact source literals are
  replaced by default; a field-scoped allowlist can retain only reviewed,
  bounded, non-sensitive business enums or constants in approved local
  destinations.
- Database profiling is read-only, allowlisted, and resource-bounded. It does
  not expose arbitrary unrestricted SQL.
- AI providers are optional. They receive safe metadata, cannot approve a
  specification, and cannot generate data directly.
- Human review remains required for ambiguous identifiers, free text, inferred
  relationships, and organization-specific privacy policy.

The project does not certify statistical anonymity, protection from every
re-identification attack, or cross-environment byte identity.

## Choose A Guide

- [Review The Output](https://wa-pis.github.io/agent-paranoid-android/getting-started/review-output/)
- [Related Tables](https://wa-pis.github.io/agent-paranoid-android/getting-started/related-tables/)
- [Safety Model](https://wa-pis.github.io/agent-paranoid-android/concepts/safety-model/)
- [CLI Command Index](https://wa-pis.github.io/agent-paranoid-android/reference/cli/)
- [Troubleshooting](https://wa-pis.github.io/agent-paranoid-android/operations/troubleshooting/)

## Development

```bash
python3 -m pip install "uv==0.11.23"
uv sync --frozen --all-extras --no-install-project
uv sync --frozen --all-extras --no-editable --no-build-isolation
uv run --no-sync scripts/check_release.sh
```

See [Contributing](CONTRIBUTING.md), [Support](SUPPORT.md),
[Governance](GOVERNANCE.md), [Code Of Conduct](CODE_OF_CONDUCT.md),
[Security Policy](SECURITY.md), [Changelog](CHANGELOG.md), and
[License](LICENSE). Releases use PyPI Trusted Publishing with verified wheels
and source distributions, checksums, SBOMs, and GitHub attestations.

## AI-Assisted Development

AI-assisted changes require human review and tests; never send production data,
raw PII, credentials, or tokens to AI. The name nods to Radiohead's "Paranoid
Android"; this project is unaffiliated.
