# Installation

## Requirements

- Python 3.11 or newer
- enough local disk space for the requested output
- a dedicated working directory for inputs and generated artifacts

## Install From PyPI

Create an isolated environment:

### macOS and Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install --upgrade pip
python3 -m pip install agent-paranoid-android
```

### Windows PowerShell

```powershell
py -3.11 -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install agent-paranoid-android
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
external system.

## Install For Development

Clone the repository and install the locked development environment:

```bash
git clone https://github.com/wa-pis/agent-paranoid-android.git
cd agent-paranoid-android
python3 -m pip install "uv==0.11.23"
uv sync --frozen --extra dev --no-install-project
uv sync --frozen --extra dev --no-editable --no-build-isolation
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

Use [First CSV Dataset](first-csv.md) for one table or
[Related Tables](related-tables.md) for a folder containing one CSV per table.
