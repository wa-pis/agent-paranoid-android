# Contributing

Thanks for helping improve Agent Paranoid Android.

This project handles potentially sensitive schemas and source files, so changes
must preserve the safety contract before they optimize ergonomics or breadth.

## Ground Rules

- Never commit real customer data, production rows, raw PII, secrets, tokens,
  credentials, private keys, or internal hostnames.
- Use synthetic fixtures such as `example.com`, `example.test`, `555-010x`, and
  small fake CSV files.
- Keep Trino access read-only, allowlisted, and bounded.
- Do not add tools that accept arbitrary unrestricted SQL.
- Generated data must be deterministic when a seed is supplied.
- Validation must be executable Python logic, not only free-form LLM reasoning.

## AI-Assisted Contributions

AI-generated and AI-assisted contributions are welcome. Contributors remain
responsible for understanding and reviewing every submitted change, verifying
licenses and provenance, adding appropriate tests, and ensuring that generated
code does not introduce secrets or unsafe behavior.

Do not send production data, raw PII, credentials, internal infrastructure
details, or other sensitive project context to external AI services. Disclose
material AI assistance in the pull request when it helps reviewers understand
the provenance or review needs of a change.

## Development Setup

Use Python 3.11 or newer.

```bash
python3 -m pip install -e ".[dev]"
```

Run the normal checks:

```bash
python3 -m ruff check src tests scripts
python3 -m mypy
python3 -m compileall -q src tests scripts
python3 -m pytest
```

Run the full release gate before proposing larger changes:

```bash
scripts/check_release.sh
```

## Change Workflow

1. Keep changes focused and small enough to review.
2. Update README and docs for user-visible behavior changes.
3. Update `CHANGELOG.md` under `Unreleased`.
4. Add or update tests for safety, validation, generation, or CLI behavior.
5. Regenerate `schemas/dataset_spec.schema.json` when `DatasetSpec` changes:

```bash
python3 scripts/export_dataset_schema.py
```

Use OpenSpec for larger behavior changes:

```text
openspec/changes/<change-id>/
```

## Pull Request Checklist

- The change does not copy source rows into generated output.
- The change does not expose raw PII in artifacts, logs, exceptions, or MCP
  responses.
- Unsafe SQL paths are rejected by tests when Trino behavior changes.
- Generated outputs remain reproducible by seed.
- New files and examples contain synthetic data only.
- AI-assisted changes have been reviewed by the contributor, and no sensitive
  project data was shared with external AI services.
- Relevant tests and `scripts/check_release.sh` pass, or the PR explains why a
  check could not be run.

## Commit Signing

Maintainer commits are SSH-signed. External contributions are welcome without a
specific signing requirement unless branch protection later enforces it.
