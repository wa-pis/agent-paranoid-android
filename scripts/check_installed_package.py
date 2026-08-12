"""Verify the installed distribution rather than the source checkout."""

from __future__ import annotations

import argparse
import csv
import importlib.util
import json
import re
import subprocess
import sys
import tempfile
from importlib.metadata import distribution, distributions
from importlib.resources import files
from pathlib import Path

from test_data_agent.version import __version__


DISTRIBUTION_NAME = "agent-paranoid-android"
EXPECTED_SCRIPTS = {
    "test-data-agent": "test_data_agent.cli:main",
    "test-data-agent-mcp-generator": "test_data_agent.mcp_generator_server:main",
    "test-data-agent-mcp-trino": "test_data_agent.mcp_trino_server:main",
}
EXPECTED_PROJECT_URLS = {
    "Documentation, https://wa-pis.github.io/agent-paranoid-android/",
    "Issues, https://github.com/wa-pis/agent-paranoid-android/issues",
    "Changelog, https://github.com/wa-pis/agent-paranoid-android/blob/main/CHANGELOG.md",
    "Release Notes, https://github.com/wa-pis/agent-paranoid-android/releases",
    (
        "Container Images, "
        "https://github.com/wa-pis/agent-paranoid-android/pkgs/container/"
        "agent-paranoid-android-cli"
    ),
}
EXPECTED_BASE_DEPENDENCIES = {"faker", "pydantic", "pyyaml"}
EXPECTED_EXTRAS = {
    "all",
    "dev",
    "gigachat",
    "mcp",
    "openai",
    "parquet",
    "postgres",
    "trino",
}
EXPECTED_RUNTIME_EXTRA_DEPENDENCIES = {
    "all": {"gigachat", "mcp", "openai", "psycopg", "pyarrow", "sqlglot", "trino"},
    "gigachat": {"gigachat"},
    "mcp": {"mcp"},
    "openai": {"openai"},
    "parquet": {"pyarrow"},
    "postgres": {"psycopg"},
    "trino": {"sqlglot", "trino"},
}
OPTIONAL_MODULES = {
    "gigachat": {"gigachat"},
    "mcp": {"mcp"},
    "openai": {"openai"},
    "parquet": {"pyarrow"},
    "postgres": {"psycopg"},
    "trino": {"sqlglot", "trino"},
}
MAX_DISTRIBUTIONS = {
    "all": 70,
    "base": 10,
    "gigachat": 20,
    "mcp": 35,
    "openai": 20,
    "parquet": 11,
    "postgres": 12,
    "trino": 25,
}
BOOTSTRAP_DISTRIBUTIONS = {"pip", "setuptools", "uv", "wheel"}
MAX_WHEEL_SIZE_BYTES = 256 * 1024


def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)
    installed = distribution(DISTRIBUTION_NAME)
    if installed.version != __version__:
        raise SystemExit(
            f"installed metadata version {installed.version!r} does not match "
            f"package version {__version__!r}"
        )

    project_urls = set(installed.metadata.get_all("Project-URL") or [])
    missing_urls = EXPECTED_PROJECT_URLS - project_urls
    if missing_urls:
        raise SystemExit(f"installed wheel is missing project URLs: {sorted(missing_urls)}")

    requirements = installed.requires or []
    dependencies_by_extra = group_dependencies_by_extra(requirements)
    base_dependencies = dependencies_by_extra.get("base", set())
    if base_dependencies != EXPECTED_BASE_DEPENDENCIES:
        raise SystemExit(
            "installed wheel has invalid base dependencies: "
            f"{sorted(base_dependencies)}"
        )
    for extra, expected in EXPECTED_RUNTIME_EXTRA_DEPENDENCIES.items():
        actual = dependencies_by_extra.get(extra, set())
        if actual != expected:
            raise SystemExit(
                f"installed wheel has invalid {extra} dependencies: "
                f"{sorted(actual)}"
            )
    extras = set(installed.metadata.get_all("Provides-Extra") or [])
    if extras != EXPECTED_EXTRAS:
        raise SystemExit(f"installed wheel has invalid extras: {sorted(extras)}")

    marker = files("test_data_agent").joinpath("py.typed")
    if not marker.is_file():
        raise SystemExit("installed wheel is missing test_data_agent/py.typed")
    demo_fixture = files("test_data_agent.resources").joinpath(
        "demo_customers.csv"
    )
    if not demo_fixture.is_file():
        raise SystemExit("installed wheel is missing the bundled demo fixture")

    scripts = {
        entry.name: entry.value
        for entry in installed.entry_points
        if entry.group == "console_scripts"
    }
    missing_or_changed = {
        name: target
        for name, target in EXPECTED_SCRIPTS.items()
        if scripts.get(name) != target
    }
    if missing_or_changed:
        raise SystemExit(f"installed wheel has invalid console scripts: {missing_or_changed}")

    verify_install_profile(args.profile)
    verify_installed_demo()
    verify_installed_csv_json_quickstart()
    if args.profile == "postgres":
        verify_installed_postgres_sql_smoke()
    if args.wheel is not None:
        verify_wheel_size(args.wheel)

    print(
        f"Installed wheel verified: {DISTRIBUTION_NAME} {installed.version} "
        f"({args.profile} profile)"
    )


def parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--profile",
        choices=sorted(MAX_DISTRIBUTIONS),
        default="base",
        help="Expected isolated installation profile.",
    )
    parser.add_argument(
        "--wheel",
        type=Path,
        help="Built wheel whose compressed size must stay within budget.",
    )
    return parser.parse_args(argv)


def group_dependencies_by_extra(
    requirements: list[str],
) -> dict[str, set[str]]:
    grouped: dict[str, set[str]] = {}
    for requirement in requirements:
        name = requirement_name(requirement)
        extras = requirement_extras(requirement)
        for extra in extras or {"base"}:
            grouped.setdefault(extra, set()).add(name)
    return grouped


def requirement_extras(requirement: str) -> set[str]:
    return set(
        re.findall(
            r"""extra\s*==\s*["']([A-Za-z0-9_.-]+)["']""",
            requirement,
        )
    )


def verify_install_profile(profile: str) -> None:
    expected_features = (
        set(OPTIONAL_MODULES)
        if profile == "all"
        else ({profile} if profile != "base" else set())
    )
    for feature, modules in OPTIONAL_MODULES.items():
        for module in modules:
            available = importlib.util.find_spec(module) is not None
            if available != (feature in expected_features):
                state = "present" if available else "missing"
                raise SystemExit(
                    f"{profile} profile has invalid optional module "
                    f"{module}: {state}"
                )

    installed_names = {
        requirement_name(str(item.metadata["Name"]))
        for item in distributions()
        if item.metadata["Name"]
    } - BOOTSTRAP_DISTRIBUTIONS
    maximum = MAX_DISTRIBUTIONS[profile]
    if len(installed_names) > maximum:
        raise SystemExit(
            f"{profile} profile exceeds dependency budget: "
            f"{len(installed_names)} installed, maximum {maximum}"
        )


def verify_wheel_size(path: Path) -> None:
    if not path.is_file() or path.suffix != ".whl":
        raise SystemExit(f"wheel path is invalid: {path}")
    size = path.stat().st_size
    if size > MAX_WHEEL_SIZE_BYTES:
        raise SystemExit(
            f"wheel exceeds size budget: {size} bytes, "
            f"maximum {MAX_WHEEL_SIZE_BYTES}"
        )


def verify_installed_demo() -> None:
    with tempfile.TemporaryDirectory(prefix="test-data-agent-demo-") as temp:
        root = Path(temp).resolve(strict=True)
        output = root / "generated"
        entrypoint = Path(sys.executable).with_name("test-data-agent")
        completed = subprocess.run(
            [entrypoint, "demo", "--output", str(output)],
            cwd=root,
            check=False,
            capture_output=True,
            text=True,
        )
        if completed.returncode != 0:
            raise SystemExit(
                "installed demo failed: "
                f"{completed.stderr.strip() or completed.stdout.strip()}"
            )
        manifest = json.loads((output / "generation_manifest.json").read_text())
        if not (
            manifest.get("synthetic") is True
            and manifest.get("source_rows_copied") is False
            and manifest.get("validation_valid") is True
        ):
            raise SystemExit("installed demo manifest failed safety validation")


def verify_installed_csv_json_quickstart(
    *,
    entrypoint: Path | None = None,
) -> None:
    cli = entrypoint or Path(sys.executable).with_name("test-data-agent")
    with tempfile.TemporaryDirectory(prefix="test-data-agent-quickstart-") as temp:
        root = Path(temp).resolve(strict=True)
        source = root / "customers.csv"
        source.write_text(
            "customer_id,email,segment\n"
            "C1,alice@example.test,retail\n"
            "C2,bob@example.test,business\n",
            encoding="utf-8",
        )
        for output_format in ("csv", "json"):
            output = root / f"generated-{output_format}" / f"customers.{output_format}"
            completed = subprocess.run(
                [
                    cli,
                    "generate-from-csv",
                    source,
                    "--count",
                    "3",
                    "--seed",
                    "12345",
                    "--format",
                    output_format,
                    "--output",
                    output,
                ],
                cwd=root,
                check=False,
                capture_output=True,
                text=True,
            )
            if completed.returncode != 0:
                raise SystemExit(
                    f"installed {output_format} quickstart failed: "
                    f"{completed.stderr.strip() or completed.stdout.strip()}"
                )
            manifest = json.loads(
                (output.parent / "generation_manifest.json").read_text()
            )
            if not (
                manifest.get("synthetic") is True
                and manifest.get("source_rows_copied") is False
                and manifest.get("validation_valid") is True
                and manifest.get("output_format") == output_format
            ):
                raise SystemExit(
                    f"installed {output_format} quickstart manifest failed "
                    "safety validation"
                )
            if output_format == "csv":
                with output.open(newline="") as handle:
                    row_count = sum(1 for _ in csv.DictReader(handle))
            else:
                rows = json.loads(output.read_text())
                row_count = len(rows) if isinstance(rows, list) else -1
            if row_count != 3:
                raise SystemExit(
                    f"installed {output_format} quickstart generated "
                    f"{row_count} rows instead of 3"
                )


def verify_installed_postgres_sql_smoke(
    *,
    entrypoint: Path | None = None,
) -> None:
    cli = entrypoint or Path(sys.executable).with_name("test-data-agent")
    with tempfile.TemporaryDirectory(prefix="test-data-agent-postgres-") as temp:
        root = Path(temp).resolve(strict=True)
        spec = root / "dataset-spec.json"
        first = root / "first.sql"
        second = root / "second.sql"
        spec.write_text(
            json.dumps(
                {
                    "entities": [
                        {
                            "name": "orders",
                            "row_count": 2,
                            "primary_key": "order_id",
                            "fields": [
                                {
                                    "name": "order_id",
                                    "data_type": "integer",
                                    "is_identifier": True,
                                },
                                {"name": "status", "data_type": "string"},
                            ],
                        }
                    ],
                    "generation_settings": {"seed": 12345},
                }
            ),
            encoding="utf-8",
        )

        help_result = subprocess.run(
            [cli, "profile-postgres", "--help"],
            cwd=root,
            check=False,
            capture_output=True,
            text=True,
        )
        if help_result.returncode != 0:
            raise SystemExit("installed PostgreSQL profile command is unavailable")

        for output in (first, second):
            completed = subprocess.run(
                [
                    cli,
                    "export-postgres-sql",
                    spec,
                    "--seed",
                    "12345",
                    "--output",
                    output,
                ],
                cwd=root,
                check=False,
                capture_output=True,
                text=True,
            )
            if completed.returncode != 0:
                raise SystemExit(
                    "installed PostgreSQL SQL export failed: "
                    f"{completed.stderr.strip() or completed.stdout.strip()}"
                )

        sql = first.read_text(encoding="utf-8")
        if sql != second.read_text(encoding="utf-8"):
            raise SystemExit("installed PostgreSQL SQL export is not deterministic")
        required = (
            "BEGIN;",
            'CREATE TABLE "orders"',
            'INSERT INTO "orders"',
            "COMMIT;",
        )
        if not all(fragment in sql for fragment in required):
            raise SystemExit("installed PostgreSQL SQL export is incomplete")


def requirement_name(requirement: str) -> str:
    match = re.match(r"[A-Za-z0-9_.-]+", requirement)
    if match is None:
        raise SystemExit(f"installed wheel has invalid requirement: {requirement!r}")
    return match.group(0).lower().replace("_", "-")


if __name__ == "__main__":
    main()
