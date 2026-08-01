"""Installation diagnostics and capability smoke checks for the CLI."""

from __future__ import annotations

import asyncio
import importlib
import json
import sys
import tempfile
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from types import ModuleType
from typing import Any, cast

from test_data_agent.cli_contract import DoctorReport
from test_data_agent.core.settings import OutputFormat
from test_data_agent.io import generate_dataset_from_example_artifacts

ModuleImporter = Callable[[str], ModuleType]
DoctorSmoke = Callable[[], None]
ParquetDoctorSmoke = Callable[[Path, Path], None]


@dataclass(frozen=True)
class CliDoctorService:
    """Inspect installation health without exposing capability failures."""

    import_module: ModuleImporter
    parquet_smoke: ParquetDoctorSmoke
    mcp_smoke: DoctorSmoke
    trino_smoke: DoctorSmoke
    openai_smoke: DoctorSmoke

    def inspect(
        self,
        *,
        skip_smoke: bool = False,
        required_extras: set[str] | None = None,
    ) -> DoctorReport:
        checks: list[str] = []
        failures: list[str] = []
        required = set(required_extras or ())
        if "all" in required:
            required.update({"parquet", "mcp", "trino", "openai"})

        if sys.version_info >= (3, 11):
            checks.append(
                f"python: ok ({sys.version_info.major}.{sys.version_info.minor})"
            )
        else:
            failures.append("python: Python 3.11 or newer is required")

        for module_name in ("faker", "pydantic", "yaml"):
            try:
                self.import_module(module_name)
            except ImportError as exc:
                failures.append(f"dependency {module_name}: missing ({exc})")
            else:
                checks.append(f"dependency {module_name}: ok")

        optional_modules = {
            "parquet": ("pyarrow",),
            "mcp": ("mcp",),
            "trino": ("sqlglot", "trino"),
            "openai": ("openai",),
        }
        for extra, module_names in optional_modules.items():
            missing = []
            for module_name in module_names:
                try:
                    self.import_module(module_name)
                except ImportError:
                    missing.append(module_name)
            if missing and extra in required:
                failures.append(
                    f"extra {extra}: missing {', '.join(missing)} "
                    f"(install agent-paranoid-android[{extra}])"
                )
            elif missing:
                checks.append(f"extra {extra}: not installed (optional)")
            else:
                checks.append(f"extra {extra}: ok")

        if not skip_smoke and not failures:
            with tempfile.TemporaryDirectory(prefix="test-data-agent-doctor-") as tmp:
                root = Path(tmp)
                fixture = root / "example_dataset"
                output = root / "generated"
                cache_dir = root / "cache"
                write_doctor_fixture(fixture)
                generate_dataset_from_example_artifacts(
                    fixture,
                    output_folder=output,
                    seed=12345,
                    count=3,
                    output_format=OutputFormat.CSV,
                    cache_dir=cache_dir,
                    use_cache=False,
                )
                manifest = json.loads((output / "generation_manifest.json").read_text())
                if (
                    manifest.get("synthetic") is True
                    and manifest.get("source_rows_copied") is False
                    and manifest.get("validation_valid") is True
                ):
                    checks.append("quickstart smoke: ok")
                else:
                    failures.append(
                        "quickstart smoke: manifest safety flags are not valid"
                    )
                self._run_capability_smokes(required, fixture, root, checks, failures)

        return DoctorReport(checks=tuple(checks), failures=tuple(failures))

    def _run_capability_smokes(
        self,
        required: set[str],
        fixture: Path,
        root: Path,
        checks: list[str],
        failures: list[str],
    ) -> None:
        smoke_checks: tuple[tuple[str, Callable[[], None]], ...] = (
            (
                "parquet",
                lambda: self.parquet_smoke(fixture, root / "generated-parquet"),
            ),
            ("mcp", self.mcp_smoke),
            ("trino", self.trino_smoke),
            ("openai", self.openai_smoke),
        )
        for extra, smoke in smoke_checks:
            if extra not in required:
                continue
            try:
                smoke()
            except Exception:
                failures.append(
                    f"capability {extra}: failed "
                    f"(reinstall agent-paranoid-android[{extra}] and retry)"
                )
            else:
                checks.append(f"capability {extra}: ok")


def run_parquet_doctor_smoke(fixture: Path, output: Path) -> None:
    generate_dataset_from_example_artifacts(
        fixture,
        output_folder=output,
        seed=12345,
        count=3,
        output_format=OutputFormat.PARQUET,
        cache_dir=output.parent / "parquet-cache",
        use_cache=False,
    )
    parquet = importlib.import_module("pyarrow.parquet")
    parquet_files = sorted(output.glob("*.parquet"))
    if len(parquet_files) != 2:
        raise RuntimeError("parquet smoke output is incomplete")
    if any(parquet.read_table(path).num_rows != 3 for path in parquet_files):
        raise RuntimeError("parquet smoke row count is invalid")
    manifest = json.loads((output / "generation_manifest.json").read_text())
    if not (
        manifest.get("synthetic") is True
        and manifest.get("source_rows_copied") is False
        and manifest.get("validation_valid") is True
        and manifest.get("output_format") == "parquet"
    ):
        raise RuntimeError("parquet smoke manifest is invalid")


def run_mcp_doctor_smoke() -> None:
    from test_data_agent.mcp_generator_transport import create_generator_mcp

    def doctor_probe() -> dict[str, bool]:
        return {"ok": True}

    server = create_generator_mcp((doctor_probe,))
    if server is None or server.name != "test-data-agent-generator":
        raise RuntimeError("generator MCP transport is unavailable")
    tools = asyncio.run(server.list_tools())
    if [tool.name for tool in tools] != ["doctor_probe"]:
        raise RuntimeError("generator MCP tool registration is invalid")


def run_trino_doctor_smoke() -> None:
    from test_data_agent import mcp_trino_server as trino_server

    config = trino_server.TrinoConfig(
        host="doctor.invalid",
        port=443,
        user="doctor",
        http_scheme="https",
        allowed_catalogs=frozenset({"doctor"}),
        allowed_schemas=frozenset({"safe"}),
        request_timeout=0.1,
    )
    sql = "SELECT synthetic_id FROM doctor.safe.synthetic_table LIMIT 1"
    if trino_server.validate_safe_select(sql, config=config) != sql:
        raise RuntimeError("Trino safe SQL validation is unavailable")
    trino_dbapi = importlib.import_module("trino.dbapi")
    connection = trino_dbapi.connect(
        host=config.host,
        port=config.port,
        user=config.user,
        http_scheme=config.http_scheme,
        request_timeout=config.request_timeout,
    )
    connection.close()


def run_openai_doctor_smoke() -> None:
    from openai import OpenAI

    from test_data_agent.providers.openai import OpenAIAdvisorClient

    sdk = OpenAI(
        api_key="doctor-local-placeholder",
        max_retries=0,
        timeout=0.1,
    )
    try:
        if not callable(getattr(sdk.responses, "parse", None)):
            raise RuntimeError("OpenAI structured responses API is unavailable")
        OpenAIAdvisorClient(client=cast(Any, sdk), model="doctor-local")
    finally:
        sdk.close()


def write_doctor_fixture(directory: Path) -> None:
    directory.mkdir()
    (directory / "customers.csv").write_text(
        "customer_id,email,segment\n"
        "C1,alice@example.test,retail\n"
        "C2,bob@example.test,business\n",
        encoding="utf-8",
    )
    (directory / "orders.csv").write_text(
        "order_id,customer_id,status,amount\nO1,C1,paid,20\nO2,C2,cancelled,30\n",
        encoding="utf-8",
    )
