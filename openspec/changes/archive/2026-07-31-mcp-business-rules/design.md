# Design: mcp-business-rules

## Approach

Reuse the deterministic rule engine already used by the CLI. Parse rule files
and inline payloads into strict Pydantic models, validate the rule contract
against the effective DatasetSpec, then pass a small typed applier into the
existing generation workflow.

## Data And Contracts

- `generate_dataset` and `export_dataset` accept optional
  `business_rules_path` or `business_rules_payload`; at most one is allowed.
- Rule models reject extra fields and enforce bounded collections and
  expression sizes.
- A preflight estimate limits row/rule evaluations before generation work.
- Formula evaluation remains AST-based and accepts only constants, field
  names, basic arithmetic, and the existing aggregate helpers.
- `generation_manifest.json` gains an optional `business_validation` summary
  with the rule fingerprint, rule count, pass/fail counts, and validity.
- `business_validation_report.json` remains the detailed artifact.
- MCP responses expose the summary and artifact path, never generated rows.

## Failure Modes

Invalid rule structure, unsupported syntax, dangling references, unsafe
sensitive literals, conflicting path/payload inputs, and oversized payloads
or evaluation budgets fail before an output bundle is created. Runtime rule
failures are represented in the validation report and manifest, with bounded
detail. Temporary generation folders continue to be removed on publication
failures.

## Alternatives

- Embedding rules into DatasetSpec 1.0 was rejected because it would require a
  schema revision and migration policy.
- Accepting free-form YAML text over MCP was rejected because structured
  payloads provide clearer validation and tighter size controls.
- Returning full rule errors inline was rejected because row-level failures can
  create large model-context payloads.
