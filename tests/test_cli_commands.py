from __future__ import annotations

import argparse
import json
from pathlib import Path

import pytest

import test_data_agent.cli_commands as cli_commands_module
from test_data_agent.cli import build_parser
from test_data_agent.cli_commands import run_dataset_command, run_utility_command
from test_data_agent.cli_contract import DoctorReport


def test_dataset_handler_does_not_claim_non_dataset_command() -> None:
    args = argparse.Namespace(command="agent-status")

    assert run_dataset_command(args) is None


def test_postgres_profile_command_loads_optional_driver(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    driver = object()
    captured: dict[str, object] = {}

    class Resolver:
        def require_module(self, module_name: str, *, extra: str, purpose: str) -> object:
            captured["dependency"] = (module_name, extra, purpose)
            return driver

    def profile_postgres(args: argparse.Namespace, *, driver: object) -> int:
        captured["output"] = args.output
        captured["driver"] = driver
        return 0

    monkeypatch.setattr(cli_commands_module, "DEFAULT_CLI_DEPENDENCY_RESOLVER", Resolver())
    monkeypatch.setattr(cli_commands_module, "profile_postgres_command", profile_postgres)
    arguments = ["profile-postgres", "--output", str(tmp_path / "profile.json")]
    args = build_parser(arguments).parse_args(arguments)

    assert run_dataset_command(args) == 0
    assert captured == {
        "dependency": ("psycopg", "postgres", "PostgreSQL profiling"),
        "output": tmp_path / "profile.json",
        "driver": driver,
    }


@pytest.mark.parametrize(
    ("adapter", "extra", "driver_module"),
    [
        ("postgres", "postgres", "psycopg"),
        ("trino", "trino", "trino"),
    ],
)
def test_query_profile_command_loads_parser_and_adapter_driver(
    adapter: str,
    extra: str,
    driver_module: str,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    driver = object()
    captured: dict[str, object] = {"dependencies": []}

    class Resolver:
        def require_module(
            self,
            module_name: str,
            *,
            extra: str,
            purpose: str,
        ) -> object:
            dependencies = captured["dependencies"]
            assert isinstance(dependencies, list)
            dependencies.append((module_name, extra, purpose))
            return driver

    def profile_query(args: argparse.Namespace, *, driver: object) -> int:
        captured["adapter"] = args.adapter
        captured["query"] = args.query
        captured["driver"] = driver
        return 0

    monkeypatch.setattr(
        cli_commands_module,
        "DEFAULT_CLI_DEPENDENCY_RESOLVER",
        Resolver(),
    )
    monkeypatch.setattr(
        cli_commands_module,
        "profile_query_command",
        profile_query,
    )
    query = tmp_path / "query.sql"
    arguments = [
        "profile-query",
        str(query),
        "--adapter",
        adapter,
        "--source-id",
        "warehouse",
        "--entity",
        "orders_view",
        "--output",
        str(tmp_path / "profile.json"),
    ]
    args = build_parser(arguments).parse_args(arguments)

    assert run_dataset_command(args) == 0
    assert captured == {
        "dependencies": [
            ("sqlglot", extra, "SQL query source profiling"),
            (driver_module, extra, "SQL query source profiling"),
        ],
        "adapter": adapter,
        "query": query,
        "driver": driver,
    }


def test_utility_handler_injects_doctor_boundary(capsys) -> None:
    captured: dict[str, object] = {}

    def inspect_doctor(
        *,
        skip_smoke: bool = False,
        required_extras: set[str] | None = None,
    ) -> DoctorReport:
        captured["skip_smoke"] = skip_smoke
        captured["required_extras"] = required_extras
        return DoctorReport(checks=("injected doctor: ok",), failures=())

    exit_code = run_utility_command(
        argparse.Namespace(
            command="doctor",
            skip_smoke=True,
            require_extra=["trino"],
        ),
        examples_text="unused",
        doctor_inspector=inspect_doctor,
    )

    assert exit_code == 0
    assert captured == {"skip_smoke": True, "required_extras": {"trino"}}
    assert capsys.readouterr().err == "injected doctor: ok\ndoctor passed\n"


def test_direct_dataset_handler_keeps_sensitive_spec_gate(tmp_path: Path) -> None:
    raw_email = "private-person@example.com"
    spec_path = tmp_path / "unsafe_spec.json"
    output_path = tmp_path / "generated"
    spec_path.write_text(
        json.dumps(
            {
                "entities": [
                    {
                        "name": "records",
                        "row_count": 1,
                        "fields": [
                            {
                                "name": "segment",
                                "data_type": "string",
                                "distribution": {
                                    "kind": "categorical",
                                    "categories": [{"value": raw_email, "count": 1}],
                                },
                            }
                        ],
                    }
                ]
            }
        )
    )
    arguments = ["generate", str(spec_path), "--output", str(output_path)]
    args = build_parser(arguments).parse_args(arguments)

    with pytest.raises(ValueError, match="raw-looking sensitive values") as exc_info:
        run_dataset_command(args)

    assert raw_email not in str(exc_info.value)
    assert not output_path.exists()
