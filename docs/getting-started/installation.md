# Installation

## Requirements

- Python 3.11 or newer
- enough local disk space for the requested output
- a dedicated working directory for inputs and generated artifacts

The supported CI matrix covers CPython 3.11, 3.12, 3.13, and 3.14. Python 3.11
remains the minimum so users can adopt newer interpreters without forcing
existing environments to upgrade. The notice and release-gate rules for
changing this matrix are defined in
[Runtime And Integration Support](../reference/support-policy.md).

## Install From PyPI

The stable release is `1.3.0`; the commands below pin that exact version for
reproducible installation.

Stable `1.3.0` remains the recommended default. To verify the patch candidate
before promotion, pin preview `1.3.1rc1` explicitly:

```bash
python3 -m pip install "agent-paranoid-android==1.3.1rc1"
```

Create an isolated environment:

### macOS and Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install --upgrade pip
python3 -m pip install "agent-paranoid-android==1.3.0"
```

The base package supports CSV, JSON, and deterministic PostgreSQL SQL export.
Add only the source and format integrations you need:

```bash
python3 -m pip install "agent-paranoid-android[parquet]==1.3.0"
python3 -m pip install "agent-paranoid-android[mcp]==1.3.0"
python3 -m pip install "agent-paranoid-android[mcp,trino]==1.3.0"
python3 -m pip install "agent-paranoid-android[postgres]==1.3.0"
python3 -m pip install "agent-paranoid-android[openai]==1.3.0"
python3 -m pip install "agent-paranoid-android[gigachat]==1.3.0"
```

The CI dependency ceilings are intentionally small enough to catch accidental
growth:

| Profile | Capability | Maximum installed distributions |
| --- | --- | ---: |
| base | CSV and JSON | 10 |
| `parquet` | Parquet files | 11 |
| `mcp` | Generator MCP server | 35 |
| `openai` | Optional structured-output advisor | 20 |
| `gigachat` | Experimental GigaChat advisor | 20 |
| `trino` | Trino client and safe SQL parser | 25 |
| `postgres` | Read-only PostgreSQL profiling driver | 12 |

These are regression budgets, not a guarantee that every platform installs the
same count. `PyArrow` is the largest optional wheel, so keep `parquet` out of
environments that do not produce Parquet files.

The `all` extra remains available for development, demos, and container builds.
It is not the recommended user installation. Use
`test-data-agent doctor --require-extra all` to verify that full environment.

The experimental GigaChat adapter is included in `1.3.0` through its
explicit `gigachat` extra. Follow
[Use The GigaChat Advisor](../how-to/gigachat.md) for authentication, mandatory
TLS verification, and the review-first workflow. The default provider remains
OpenAI.

## Accepted Candidate Baseline

Stable `1.3.0` remains the recommended default and includes the database-source
additions accepted in `1.3.0rc1` without additional runtime changes. Add an
optional extra to the same exact stable pin only when needed.

### Windows PowerShell

```powershell
py -3.11 -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install "agent-paranoid-android==1.3.0"
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

`doctor` creates its sample input and output under a temporary directory. It
does not need a repository checkout and does not contact Trino or another
external system. `doctor --require-extra parquet` also writes and reads a
temporary Parquet bundle to verify that capability rather than only importing
PyArrow. `doctor --require-extra mcp` verifies local generator tool
registration without starting a server or opening a network connection.
`doctor --require-extra trino` parses an allowlisted read-only query and
constructs then closes a local client object without executing SQL or
contacting a Trino coordinator.
`doctor --require-extra postgres` verifies that the optional PostgreSQL driver
is installed without opening a connection.
`doctor --require-extra openai` constructs and closes a local SDK client with
a non-secret placeholder, then verifies the structured Responses API and
advisor adapter without contacting the provider.
`doctor --require-extra gigachat` validates strict structured-response mapping
and cleanup through a local fake SDK client. It does not resolve credentials,
obtain an access token, or contact GigaChat.

For CI, add `--json` to receive one versioned stdout document. For interactive
shells, generate completion from the installed command inventory:

```bash
test-data-agent completion bash
test-data-agent completion zsh
test-data-agent completion fish
test-data-agent completion powershell
```

The command prints a script; it does not modify shell startup files.

## Install For Development

Clone the repository and install the locked development environment:

```bash
git clone https://github.com/wa-pis/agent-paranoid-android.git
cd agent-paranoid-android
python3 -m pip install "uv==0.11.23"
uv sync --frozen --all-extras --no-install-project
uv sync --frozen --all-extras --no-editable --no-build-isolation
```

Run the release-quality checks:

```bash
uv run --no-sync scripts/check_release.sh
```

Build the documentation in its isolated dependency group:

```bash
uv sync --frozen --only-group docs --no-install-project
uv run --no-sync mkdocs build --strict
```

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
