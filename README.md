# Agent Paranoid Android

[![PyPI](https://img.shields.io/pypi/v/agent-paranoid-android.svg)](https://pypi.org/project/agent-paranoid-android/)
[![CI](https://github.com/wa-pis/agent-paranoid-android/actions/workflows/ci.yml/badge.svg)](https://github.com/wa-pis/agent-paranoid-android/actions/workflows/ci.yml)
[![Documentation](https://img.shields.io/badge/docs-GitHub%20Pages-blue.svg)](https://wa-pis.github.io/agent-paranoid-android/)
[![OpenSSF Scorecard](https://api.scorecard.dev/projects/github.com/wa-pis/agent-paranoid-android/badge)](https://scorecard.dev/viewer/?uri=github.com/wa-pis/agent-paranoid-android)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

Safety-first, deterministic synthetic test data generation from CSV structure,
safe profiles, reviewed `DatasetSpec` files, and allowlisted Trino metadata.
Source rows are profiled, never shuffled or copied into generated output.

**[Read the documentation](https://wa-pis.github.io/agent-paranoid-android/)**
for tutorials, concepts, configuration, MCP setup, and troubleshooting.

Current package version: `0.6.0`. The package is
`agent-paranoid-android`; the CLI is `test-data-agent`.

## Install

Python 3.11 or newer is required.

```bash
python3 -m pip install agent-paranoid-android
test-data-agent doctor
```

## Quickstart

Clone the repository to use its safe fictional fixture:

```bash
git clone https://github.com/wa-pis/agent-paranoid-android.git
cd agent-paranoid-android

test-data-agent generate-from-csv tests/fixtures/customers.csv \
  --count 25 \
  --seed 12345 \
  --format csv \
  --output out/customers.csv
```

A successful run reports:

```text
Generated synthetic dataset: out | rows: customers=25 | seed: 12345 | validation: passed | source rows copied: no
```

The output folder contains the generated data plus:

- `csv_profile.json`;
- `dataset_spec.json`;
- `validation_report.json`;
- `generation_manifest.json`.

Review the manifest and effective spec before accepting a new dataset.

## Choose A Guide

| Goal | Documentation |
| --- | --- |
| Generate from one CSV | [First CSV Dataset](https://wa-pis.github.io/agent-paranoid-android/getting-started/first-csv/) |
| Generate related tables | [Related Tables](https://wa-pis.github.io/agent-paranoid-android/getting-started/related-tables/) |
| Review specs and output | [Review The Output](https://wa-pis.github.io/agent-paranoid-android/getting-started/review-output/) |
| Add deterministic business rules | [Business Rules](https://wa-pis.github.io/agent-paranoid-android/how-to/business-rules/) |
| Connect an AI client | [MCP Setup](https://wa-pis.github.io/agent-paranoid-android/how-to/mcp/) |
| Understand the trust boundaries | [Safety Model](https://wa-pis.github.io/agent-paranoid-android/concepts/safety-model/) |
| Configure limits and Trino | [Configuration](https://wa-pis.github.io/agent-paranoid-android/reference/configuration/) |
| Recover from an error | [Troubleshooting](https://wa-pis.github.io/agent-paranoid-android/operations/troubleshooting/) |
| Upgrade from 0.5.x | [Migrating To 0.6](https://wa-pis.github.io/agent-paranoid-android/operations/migrating-to-0.6/) |

## Safety

The project derives bounded metadata such as field types, null ratios, ranges,
masked patterns, and safe low-cardinality distributions. It rejects or bounds:

- raw detected PII, credentials, tokens, and private keys in profiles;
- source-row copying and source/output path reuse;
- path traversal and symlink escapes through generator MCP tools;
- unrestricted SQL and write operations through Trino tools;
- oversized input, output, rule, query, and generation work.

Human review is still required for ambiguous identifiers, rare free text,
inferred relationships, and organization-specific privacy policy.

## Development

```bash
python3 -m pip install "uv==0.11.23"
uv sync --frozen --extra dev --no-install-project
uv sync --frozen --extra dev --no-editable --no-build-isolation
uv run --no-sync scripts/check_release.sh
```

See [Contributing](CONTRIBUTING.md), [Security Policy](SECURITY.md), and
[Changelog](CHANGELOG.md).

Releases use tokenless PyPI Trusted Publishing and include verified wheel and
source distributions, checksums, SBOMs, and GitHub attestations.

## AI-Assisted Development

This project is developed with substantial assistance from AI coding tools.
All changes remain subject to human review, automated testing, and the same
security requirements as manually written code. Do not send production data,
raw PII, credentials, or tokens to an AI system while working with the project.

The name is a nod to Radiohead's "Paranoid Android". This project is
unaffiliated with Radiohead or related rights holders.

## License

[MIT](LICENSE)
