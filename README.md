# Agent Paranoid Android

[![PyPI](https://img.shields.io/pypi/v/agent-paranoid-android.svg)](https://pypi.org/project/agent-paranoid-android/)
[![CI](https://github.com/wa-pis/agent-paranoid-android/actions/workflows/ci.yml/badge.svg)](https://github.com/wa-pis/agent-paranoid-android/actions/workflows/ci.yml)
[![Documentation](https://img.shields.io/badge/docs-GitHub%20Pages-blue.svg)](https://wa-pis.github.io/agent-paranoid-android/)
[![OpenSSF Scorecard](https://api.scorecard.dev/projects/github.com/wa-pis/agent-paranoid-android/badge)](https://scorecard.dev/viewer/?uri=github.com/wa-pis/agent-paranoid-android)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](https://github.com/wa-pis/agent-paranoid-android/blob/main/LICENSE)

Safety-first, deterministic synthetic test data generation from CSV structure,
safe profiles, reviewed specifications, and allowlisted Trino metadata.

Agent Paranoid Android preserves useful schema, distributions, relationships,
and business rules while generating fresh values from an explicit seed. It
does not shuffle or copy source rows into generated output.

Current package version: `0.5.1`. The package is
`agent-paranoid-android`; the CLI is `test-data-agent`.

## Install

Python 3.11 or newer is required.

```bash
python3 -m pip install agent-paranoid-android
test-data-agent doctor
```

A healthy installation ends with:

```text
quickstart smoke: ok
doctor passed
```

## First Dataset

Clone the repository for a safe checked-in fixture:

```bash
git clone https://github.com/wa-pis/agent-paranoid-android.git
cd agent-paranoid-android
```

Generate 25 synthetic customer rows:

```bash
test-data-agent generate-from-csv tests/fixtures/customers.csv \
  --count 25 \
  --seed 12345 \
  --format csv \
  --output out/customers.csv
```

Expected summary:

```text
Generated synthetic dataset: out | rows: customers=25 | seed: 12345 | validation: passed | source rows copied: no
```

The command also writes safe profile metadata, the effective generation
specification, a validation report, and `generation_manifest.json`.

For related tables:

```bash
test-data-agent generate-from-example tests/fixtures/example_dataset \
  --count 25 \
  --seed 12345 \
  --format csv \
  --output out/example_dataset
```

Review the manifest before accepting output:

```bash
python3 -c "import json; m=json.load(open('out/example_dataset/generation_manifest.json')); print(m['synthetic'], m['source_rows_copied'], m['validation_valid'], m['seed'])"
```

Expected:

```text
True False True 12345
```

## Choose A Guide

| Goal | Guide |
| --- | --- |
| Install and verify the package | [Installation](https://wa-pis.github.io/agent-paranoid-android/getting-started/installation/) |
| Generate from one CSV | [First CSV Dataset](https://wa-pis.github.io/agent-paranoid-android/getting-started/first-csv/) |
| Generate related tables | [Related Tables](https://wa-pis.github.io/agent-paranoid-android/getting-started/related-tables/) |
| Understand the generated files | [Review The Output](https://wa-pis.github.io/agent-paranoid-android/getting-started/review-output/) |
| Enforce domain constraints | [Business Rules](https://wa-pis.github.io/agent-paranoid-android/how-to/business-rules/) |
| Connect an AI client | [MCP Setup](https://wa-pis.github.io/agent-paranoid-android/how-to/mcp/) |
| Configure limits and Trino | [Configuration](https://wa-pis.github.io/agent-paranoid-android/reference/configuration/) |
| Recover from an error | [Troubleshooting](https://wa-pis.github.io/agent-paranoid-android/operations/troubleshooting/) |

The documentation source is under
[`docs/`](https://github.com/wa-pis/agent-paranoid-android/tree/main/docs).

## Safety Model

Source data is used only to derive bounded structural metadata such as:

- field names and inferred types;
- null ratios, approximate distinct counts, ranges, and percentiles;
- safe low-cardinality distributions for non-sensitive fields;
- masked sensitive patterns;
- inferred relationship and constraint candidates.

The project rejects or bounds:

- raw detected PII, credentials, tokens, and private keys in safe profiles and
  business-rule literals;
- source-row copying and source/output path reuse;
- path traversal and symlink escapes through generator MCP tools;
- unrestricted SQL, DDL, DML, joins, CTEs, subqueries, and unbounded results
  through Trino tools;
- oversized files, rows, columns, cells, YAML graphs, Parquet expansion,
  generated bundles, rule work, query work, and generation time.

Human review is still required for ambiguous domain identifiers, rare free
text, inferred relationships, and organization-specific privacy policy.

Read the complete
[Safety Model](https://wa-pis.github.io/agent-paranoid-android/concepts/safety-model/)
before using production-adjacent metadata.

## Business Rules

Business logic is structured YAML or JSON and enforced by deterministic code:

```yaml
field_rules:
  - table: orders
    field: status
    required: true
    allowed_values: [paid, cancelled]

row_rules:
  - type: formula
    table: orders
    field: amount
    expression: quantity * unit_price
```

Pass reviewed rules with `--business-rules`. The manifest records the
normalized rule fingerprint and validation summary.

## MCP Servers

Start the workspace-bounded generator server:

```bash
TEST_DATA_AGENT_WORKSPACE_ROOT=/path/to/workspace \
  test-data-agent-mcp-generator
```

Start the read-only Trino server with explicit allowlists:

```bash
TRINO_ALLOWED_CATALOGS=hive,iceberg \
TRINO_ALLOWED_SCHEMAS=test_data,staging \
  test-data-agent-mcp-trino
```

MCP responses return summaries and artifact paths, not source or generated
dataset rows. HTTPS is the Trino default; plain HTTP requires an explicit local
override.

## Development

The repository uses a committed `uv.lock`:

```bash
python3 -m pip install "uv==0.11.23"
uv sync --frozen --extra dev --no-install-project
uv sync --frozen --extra dev --no-editable --no-build-isolation
uv run --no-sync scripts/check_release.sh
```

See [Contributing](https://github.com/wa-pis/agent-paranoid-android/blob/main/CONTRIBUTING.md),
[Security Policy](https://github.com/wa-pis/agent-paranoid-android/security/policy),
[Changelog](https://github.com/wa-pis/agent-paranoid-android/blob/main/CHANGELOG.md),
and [Roadmap](https://wa-pis.github.io/agent-paranoid-android/roadmap/).

Releases build wheel and source distributions, verify the installed wheel,
publish SBOMs and checksums, create GitHub attestations, and use tokenless
PyPI Trusted Publishing. A post-publish job compares public PyPI digests with
GitHub Release artifacts and tests the exact public package.

## AI-Assisted Development

This project is developed with substantial assistance from AI coding tools.
All changes remain subject to human review, automated testing, and the same
security requirements as manually written code. Do not send production data,
raw PII, credentials, or tokens to an AI system while working with the project.

The name is a nod to
[Radiohead](https://www.radiohead.com/deadairspace/) and
["Paranoid Android"](https://music.apple.com/us/song/1097861770). This project
is unaffiliated with Radiohead or related rights holders.

## License

[MIT](https://github.com/wa-pis/agent-paranoid-android/blob/main/LICENSE)
