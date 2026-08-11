# Agent Paranoid Android

[![PyPI](https://img.shields.io/pypi/v/agent-paranoid-android.svg)](https://pypi.org/project/agent-paranoid-android/)
[![CI](https://github.com/wa-pis/agent-paranoid-android/actions/workflows/ci.yml/badge.svg)](https://github.com/wa-pis/agent-paranoid-android/actions/workflows/ci.yml)
[![Documentation](https://img.shields.io/badge/docs-GitHub%20Pages-blue.svg)](https://wa-pis.github.io/agent-paranoid-android/)
[![OpenSSF Scorecard](https://api.scorecard.dev/projects/github.com/wa-pis/agent-paranoid-android/badge)](https://scorecard.dev/viewer/?uri=github.com/wa-pis/agent-paranoid-android)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

Safety-first, deterministic synthetic test data generation from CSV structure,
safe profiles, reviewed `DatasetSpec` files, and allowlisted Trino metadata. The
CLI and Python library are primary; MCP, Trino, and AI providers are optional
integrations. The base package supports CSV/JSON workflows without installing
the Trino client, SQL parser, or MCP SDK.
Source rows are profiled, never shuffled or copied into generated output.

**[Read the documentation](https://wa-pis.github.io/agent-paranoid-android/)** for tutorials, concepts, configuration, MCP setup, and troubleshooting.
Current version: `1.0.0rc6`. Package: `agent-paranoid-android`; CLI: `test-data-agent`.

## What It Preserves

From bounded evidence and a reviewed `DatasetSpec`, generation can preserve schema
and types, nullability, ranked distribution and scale shape, approved FK graphs,
temporal dependencies, and executable business rules. AI may propose relationships
and rules; human review and deterministic validation remain the authority boundary.

It intentionally does not preserve or copy source values or real PII. It does not
certify statistical anonymity, protection from every re-identification attack, or
cross-environment byte identity. A seed provides logical reproducibility under the
recorded package, dependency, locale, and serializer environment.

## Install

Python 3.11 or newer is required. CI tests CPython 3.11 through 3.14. After
publication, install the exact RC6 candidate used for acceptance:

```bash
python3 -m pip install "agent-paranoid-android==1.0.0rc6"
test-data-agent doctor
```

Install only features you use:

```bash
python3 -m pip install "agent-paranoid-android[parquet]==1.0.0rc6"
python3 -m pip install "agent-paranoid-android[mcp]==1.0.0rc6"
python3 -m pip install "agent-paranoid-android[trino]==1.0.0rc6"
python3 -m pip install "agent-paranoid-android[mcp,trino]==1.0.0rc6"
python3 -m pip install "agent-paranoid-android[openai]==1.0.0rc6"
```

The `trino` extra is required only for Trino profiling and contains the Trino
client and safe SQL parser. Add `mcp` when using the Trino MCP server.
The default aggregate-only tools return summaries, not source rows. The explicit opt-in row-returning tools include
`run_safe_select`, which requires `TRINO_ENABLE_SAFE_SELECT=true`; bounded, masked rows may contain allowed source values and are not source-free, PII-free, anonymous, or privacy-safe.

## First Offline Run

Run the installed package with its bundled fictional customer fixture. No checkout,
network, Trino, MCP, or provider is required:

```bash
test-data-agent demo --output out/demo
```

A successful run reports:

```text
Generated synthetic dataset: out/demo | rows: customers=12 | seed: 20260801 | validation: passed | source rows copied: no
```

Representative deterministic output:

```csv
customer_id,email,segment,signup_date
syn_customers_00000001,amber21@example.test,category_1,2024-02-10
```

The demo preserves evidenced column names and types, non-null shape, category rank,
and date range. Its fixture has no relationship or business-rule evidence, so the
demo makes no claim about those properties. The output folder contains:

- `customers.csv`;
- `csv_profile.json`;
- `dataset_spec.json`;
- `validation_report.json`;
- `generation_manifest.json`.

The destination must not already exist. Review the manifest and effective spec before
accepting any dataset. Then follow [First CSV Dataset](https://wa-pis.github.io/agent-paranoid-android/getting-started/first-csv/)
to profile your own input.

## Choose A Guide

| Goal | Documentation |
| --- | --- |
| Validate the workflow with a real development or analytics task | [Product Validation Pilot](https://wa-pis.github.io/agent-paranoid-android/getting-started/product-validation-pilot/) |
| Generate from one CSV | [First CSV Dataset](https://wa-pis.github.io/agent-paranoid-android/getting-started/first-csv/) |
| Generate related tables | [Related Tables](https://wa-pis.github.io/agent-paranoid-android/getting-started/related-tables/) |
| Review specs and output | [Review The Output](https://wa-pis.github.io/agent-paranoid-android/getting-started/review-output/) |
| Add deterministic business rules | [Business Rules](https://wa-pis.github.io/agent-paranoid-android/how-to/business-rules/) |
| Use the review-first agent flow | [Agent Design](https://wa-pis.github.io/agent-paranoid-android/agent_design/) |
| Connect an AI client or provider | [AI Integration](https://wa-pis.github.io/agent-paranoid-android/ai_integration/) · [Provider Adapter](https://wa-pis.github.io/agent-paranoid-android/how-to/custom-advisor-provider/) · [Runnable MCP example](examples/mcp_stdio/) |
| Run isolated OCI images | [Container Deployment](https://wa-pis.github.io/agent-paranoid-android/operations/containers/) |
| Understand the trust boundaries | [Safety Model](https://wa-pis.github.io/agent-paranoid-android/concepts/safety-model/) |
| Configure limits and Trino | [Configuration](https://wa-pis.github.io/agent-paranoid-android/reference/configuration/) · [Runnable local Trino example](examples/local_trino/) |
| Inspect CSV, JSON, SQL, and Parquet output | [Runnable output-format example](examples/output_formats/); PostgreSQL: `test-data-agent export-postgres-sql dataset_spec.yaml --seed 12345 -o out/dataset.sql` |
| Recover from an error | [Troubleshooting](https://wa-pis.github.io/agent-paranoid-android/operations/troubleshooting/) |
| Decide whether this tool fits | [Choose An Approach](https://wa-pis.github.io/agent-paranoid-android/concepts/choosing-an-approach/) |

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
uv sync --frozen --all-extras --no-install-project
uv sync --frozen --all-extras --no-editable --no-build-isolation
uv run --no-sync scripts/check_release.sh
```

See [Contributing](CONTRIBUTING.md), [Support](SUPPORT.md), [Governance](GOVERNANCE.md),
[Code Of Conduct](CODE_OF_CONDUCT.md), [Security Policy](SECURITY.md), [Changelog](CHANGELOG.md), and [License](LICENSE).

Releases use tokenless PyPI Trusted Publishing with verified wheels/source distributions, checksums, SBOMs, and GitHub attestations.

## AI-Assisted Development

AI-assisted changes require human review and tests; never send production data, raw PII, credentials, or tokens to AI. The name nods to Radiohead's "Paranoid Android"; this project is unaffiliated.
