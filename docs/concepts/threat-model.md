# Threat Model

This model covers supported CSV, Python, CLI, MCP, Trino, advisor, generation,
validation, and export workflows. The primary security objective is to prevent
source rows, raw detected PII, and secrets from crossing into generated output,
provider requests, logs, or unrestricted database operations.

## Assets And Trust Boundaries

Protected assets are source datasets, credentials, connection settings,
reviewed specifications, generated artifacts, manifests, and validation
reports. Treat every source file, rule payload, profile, path, Trino response,
MCP request, advisor response, and output destination as untrusted.

The main boundaries are:

- local source to bounded profiler;
- profiler and reviewed specification to deterministic generator;
- application to optional AI provider;
- MCP client to workspace-confined tools;
- application to read-only Trino;
- staged artifacts to the published output directory.

## Threats And Controls

| Threat | Control | Residual risk |
| --- | --- | --- |
| Source rows or raw PII reach generated output | Profiles suppress sensitive values; specs pass `assert_spec_safe()`; supported CSV flows reject complete-row reuse. | Partial values, rare combinations, and statistical similarity require human review. |
| Secrets leak through input, configuration, logs, or provider calls | Secret-like fields and values are treated as sensitive; provider requests use bounded structured evidence; rejected values are not echoed. | Unknown secret formats or unsafe downstream logging can bypass heuristics. |
| Prompt injection in source text or advisor output changes authority | Source text is untrusted data, provider schemas are validated, and AI proposals require explicit human review; deterministic code alone authorizes generation and validation. | A reviewer can still approve a misleading proposal. Never send raw production content to a provider. |
| Provider receives source records or rare identifying values | Advisor payloads exclude rows, replace categories with synthetic labels, and sanitize singleton values before the provider boundary. | Provider retention and transport remain governed by the selected provider and operator configuration. |
| Trino access reads sensitive rows or mutates data | Public operations are allowlisted, read-only, and bounded; unsafe SQL is rejected before execution; credentials stay outside returned payloads. | Database permissions must independently enforce least privilege and read-only access. |
| MCP paths escape the configured workspace or overwrite trusted files | Path traversal and symlink escapes are rejected; source and output paths must differ; publication is staged and atomic. | Operators must secure the workspace and downstream artifact storage. |
| Generated artifacts are mistaken for privacy-certified data | Manifests record synthetic and validation evidence; documentation separates structural validation from privacy assurance. | The project provides no differential privacy, anonymity, or universal re-identification guarantee. |
| Oversized inputs, queries, rules, or output exhaust resources | Byte, row, cell, nesting, query, rule, disk, output, and wall-clock budgets fail closed. | Limits reduce impact but do not replace process, container, or infrastructure quotas. |
| Modified packages or artifacts enter the release path | Release gates produce checksums, SBOMs, attestations, and exact-commit evidence. | Users must verify published evidence and protect their installation environment. |

## Assumptions And Non-Goals

Operators keep credentials outside datasets and logs, grant Trino least
privilege, review inferred rules, and protect generated artifacts. The project
does not defend a compromised host, malicious Python code running in the same
process, a compromised dependency, or redistribution by an authorized user.
It does not certify legal compliance or statistical privacy.

Report suspected boundary failures through the private process in the
[Security Policy](https://github.com/wa-pis/agent-paranoid-android/security/policy).
Use synthetic reproductions only.
