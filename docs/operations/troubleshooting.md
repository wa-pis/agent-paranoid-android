# Troubleshooting

Start with:

```bash
test-data-agent doctor
```

The final line should be `doctor passed`.

## Command Not Found

Symptom:

```text
test-data-agent: command not found
```

Activate the environment where the package was installed:

```bash
source .venv/bin/activate
python3 -m pip show agent-paranoid-android
```

On Windows PowerShell:

```powershell
.venv\Scripts\Activate.ps1
python -m pip show agent-paranoid-android
```

## Output Already Exists

Folder bundles require a new or empty directory. Choose a new path:

```bash
test-data-agent generate-from-example data/example_dataset \
  --count 25 \
  --seed 12345 \
  --format csv \
  --output out/run-002
```

Use `--overwrite` only for commands that explicitly support replacing a
single-file output. Never point output at a source file or source folder.

## Input Limit Exceeded

The error names the failed limit. Prefer splitting an oversized source or
reducing requested rows before raising the corresponding environment variable.

When a limit must change, set the smallest value that supports the reviewed
workload and keep output and wall-clock limits in proportion.

See [Configuration](../reference/configuration.md).

## Sensitive Value Rejected

Profiles and business rules reject values that resemble PII, credentials,
tokens, or private keys.

Do not bypass the detector by encoding or fragmenting a production value.
Replace it with a semantic rule, a reserved example value, or a generator
strategy.

## Validation Failed

Open:

- `validation_report.json`;
- `business_validation_report.json`, when present;
- the effective spec and rule file.

Check the first failing section before changing generation settings. Common
causes are an incorrect inferred relationship, impossible field ranges,
conflicting formulas, and a business rule that references the wrong field.

Negative and mixed modes can fail validation intentionally. Keep their output
separate and label it as invalid test data.

## Results Are Not Reproducible

Confirm that both runs use the same:

- package version;
- `DatasetSpec` and its fingerprint;
- business-rule file and fingerprint;
- seed;
- row count, mode, invalid ratio, and format.

File ordering and output encoding should also be compared on the same supported
platform.

## Trino Allowlists Are Required

Set both variables:

```bash
export TRINO_ALLOWED_CATALOGS=hive,iceberg
export TRINO_ALLOWED_SCHEMAS=test_data,staging
```

Do not use `TRINO_ALLOW_UNRESTRICTED=true` merely to silence configuration
errors.

## Plain HTTP Is Disabled

Use HTTPS for remote Trino. For an isolated local integration instance only:

```bash
export TRINO_HTTP_SCHEME=http
export TRINO_ALLOW_INSECURE_HTTP=true
```

## MCP Path Rejected

Move the input or output below `TEST_DATA_AGENT_WORKSPACE_ROOT`. A textual path
that appears to be inside the workspace can still be rejected when an existing
symlink resolves outside it.

Use a real directory with no symlink boundary and request a new output path.

## Reporting A Security Problem

Do not open a public issue containing exploit details, source data, PII, or
credentials. Follow the repository
[security policy](https://github.com/wa-pis/agent-paranoid-android/security/policy).
