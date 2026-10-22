# Installation

Stable `1.6.0` is the recommended release. Its signed source, packages and
containers passed [public verification](../release-evidence-1.6.0.md).

## Requirements

- Python 3.11 or newer
- enough local disk space for the requested output
- a dedicated working directory for inputs and generated artifacts

The supported CI matrix covers CPython 3.11, 3.12, 3.13, and 3.14. Python 3.11
remains the minimum so users can adopt newer interpreters without forcing
existing environments to upgrade. The notice and release-gate rules for
changing this matrix are defined in
[Runtime And Integration Support](../reference/support-policy.md).

Read the
[migration notes](../reference/generation-contract-migration.md) before
regenerating existing fixtures.

## Install From PyPI

The stable release is `1.6.0`; the commands below
pin that exact version for reproducible installation.

Create an isolated environment:

### macOS and Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install --upgrade pip
python3 -m pip install "agent-paranoid-android==1.6.0"
```

The base package supports CSV, JSON, and deterministic PostgreSQL SQL export.
Add only the source and format integrations you need:

```bash
python3 -m pip install "agent-paranoid-android[parquet]==1.6.0"
python3 -m pip install "agent-paranoid-android[mcp]==1.6.0"
python3 -m pip install "agent-paranoid-android[mcp,trino]==1.6.0"
python3 -m pip install "agent-paranoid-android[postgres]==1.6.0"
python3 -m pip install "agent-paranoid-android[openai]==1.6.0"
python3 -m pip install "agent-paranoid-android[gigachat]==1.6.0"
```

Dependency footprint budgets live in [Dependency Compatibility](../reference/dependency-compatibility.md#installation-footprint).

The `all` extra remains available for development, demos, and container builds.
It is not the recommended user installation. Use
`test-data-agent doctor --require-extra all` to verify that full environment.

The experimental GigaChat adapter is retained in `1.6.0` through its
explicit `gigachat` extra. Follow
[Use The GigaChat Advisor](../how-to/gigachat.md) for authentication, mandatory
TLS verification, and the review-first workflow. The default provider remains
OpenAI.

<a id="accepted-candidate-baseline"></a>

Stable `1.6.0` is the recommended default. Add an optional extra to the same
exact stable pin only when needed.

### Windows PowerShell

```powershell
py -3.11 -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install "agent-paranoid-android==1.6.0"
```

Run the self-contained environment check:

```bash
test-data-agent doctor
```

Expected final lines:

```text
quickstart smoke: ok
doctor passed
```

`doctor` uses a temporary fictional fixture and makes no external calls.
Use `doctor --require-extra parquet` (or another installed extra) for an offline
capability check. See [Troubleshooting](../operations/troubleshooting.md) for
individual checks and [CLI automation](../reference/cli-automation.md) for JSON
output.

<a id="install-for-development"></a>

For development setup use [Contributing](https://github.com/wa-pis/agent-paranoid-android/blob/main/CONTRIBUTING.md).
For documentation builds use [Publishing Documentation](../development/documentation.md).
Shell completion has its own [reference](../reference/shell-completion.md).

## Confirm The Installed Version

```bash
python3 -c "import test_data_agent; print(test_data_agent.__version__)"
```

The package name is `agent-paranoid-android`. The command remains
`test-data-agent`.

## Next Step

Use [First CSV Dataset](first-csv.md) for one table,
[Related Tables](related-tables.md) for a folder containing one CSV per table,
or [Profile PostgreSQL](../how-to/postgresql.md) for an allowlisted database.
