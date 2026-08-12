# Troubleshooting

Start with:

```bash
test-data-agent doctor
```

The final line should be `doctor passed`.

Require the optional capability you intend to operate:

```bash
test-data-agent doctor --require-extra parquet
```

For Parquet this performs a local temporary generation and read-back, checks
row counts and manifest safety flags, and contacts no external service. A
failure recommends the exact extra to reinstall without exposing the original
exception text or temporary paths.

`doctor --require-extra mcp` constructs the real generator `FastMCP`
transport, registers one local audited probe tool, and verifies its public tool
listing. It does not start a server, listen on a port, invoke the tool, or
contact an MCP client.

`doctor --require-extra trino` validates a bounded allowlisted query with the
installed Trino SQL parser, constructs a client for the reserved
`doctor.invalid` host, and closes it without opening a cursor or executing SQL.
It does not read Trino credentials or contact a coordinator. On failure,
reinstall `agent-paranoid-android[trino]` before checking deployment-specific
allowlists and credentials.

`doctor --require-extra openai` constructs and closes the installed SDK client
with a local non-secret placeholder and verifies the structured Responses API
used by the advisor adapter. It does not read `OPENAI_API_KEY`, send a request,
or contact the provider. On failure, reinstall
`agent-paranoid-android[openai]` before checking deployment credentials.

`doctor --require-extra gigachat` uses a local fake SDK client to verify strict
structured-response mapping and cleanup. It does not read
`GIGACHAT_CREDENTIALS` or `GIGACHAT_ACCESS_TOKEN`, obtain a token, or contact
GigaChat. Before the next minor release candidate, run it only from a source
checkout installed with `.[gigachat]`; published `1.0.0` does not contain the
extra.

## GigaChat Advice Failed

Check the fixed local category first: missing extra, authentication, scope,
TLS/CA bundle, rate limit, timeout, filtered response, invalid response, or
unavailable service. Remote response bodies and SDK exception text are
intentionally suppressed because they may reflect credentials or request
metadata.

Configure exactly one of `GIGACHAT_CREDENTIALS` and
`GIGACHAT_ACCESS_TOKEN`. Match `GIGACHAT_SCOPE` to the API project, keep TLS
verification enabled, and use `GIGACHAT_CA_BUNDLE_FILE` only for a reviewed
readable CA bundle. Do not work around a certificate failure with an insecure
SDK example. A failed provider call leaves the workspace awaiting review and
does not create generated rows; retry only after correcting the local cause.

GigaChat's structured-output feature is currently beta. The adapter performs a
single local baseline-compatibility pass only after initial structured
validation fails, then reruns every normal validation. If `invalid response`
persists, the remaining provider proposal is not safe to review; use another
supported model or retry later instead of weakening validation.

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
single-file output or a single-entity bundle. For a bundle it approves
replacement of every same-named sibling artifact, not only the generated row
file. Never point output at a source file or source folder.

## Agent Approval Was Interrupted

Inspect the workspace:

```bash
test-data-agent agent-status out/agent
```

When it reports `recovery_required`, run the exact `agent-recover` command it
prints. Recovery requires the previously reviewed DatasetSpec SHA-256,
revalidates the existing generated bundle, and does not generate new rows.

Do not edit files under `generated/` before recovery. A changed checkpoint,
manifest, report, spec, profile, or row file causes recovery to fail closed.

## Process Or Host Stopped During Publication

For an agent workspace, run `agent-status` first. Use `agent-recover` only when
the status reports `recovery_required`; it revalidates the existing generated
bundle before publishing missing completion metadata.

For a non-agent generation command, do not treat a hidden staging directory or
a destination without its expected manifest and validation report as success.
Confirm that no generation process is still running, retain the incomplete
files for investigation when needed, and rerun with the same reviewed inputs
and seed into a new destination.

Where an atomic state writer or staged bundle publication is used, replacement
prevents readers from observing its partial state during normal operation.
Standalone artifact commands are not one global transaction, and artifact
files and parent directories are not flushed with `fsync`. A hard process
stop, host or storage failure, or power loss can therefore leave staging data
or lose a recent artifact. Use storage with the durability and backup
guarantees required by the deployment.

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
