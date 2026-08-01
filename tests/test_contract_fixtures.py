from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import test_data_agent
from test_data_agent.advisor import AdvisorExchange
from test_data_agent.agent import AgentResult
from test_data_agent.core import DatasetSpec
from test_data_agent.io import GenerationManifest
from test_data_agent.validation import DatasetValidationReport

from scripts.contract_fixtures import (
    CONTRACT_FIXTURE_NAMES,
    build_contract_fixtures,
)


CONTRACT_FIXTURE_DIR = Path("tests/fixtures/contracts")


def test_public_contract_fixtures_are_current(tmp_path: Path) -> None:
    actual = build_contract_fixtures(tmp_path)
    assert {path.name for path in CONTRACT_FIXTURE_DIR.glob("*.json")} == set(
        CONTRACT_FIXTURE_NAMES
    )
    expected = {
        name: json.loads(
            CONTRACT_FIXTURE_DIR.joinpath(name).read_text(encoding="utf-8")
        )
        for name in CONTRACT_FIXTURE_NAMES
    }

    assert actual == expected, (
        "public contract fixture changed; review compatibility and run "
        "python3 scripts/update_contract_fixtures.py"
    )


def test_public_contract_fixtures_remain_typed_and_row_free() -> None:
    cli_plan = _load_fixture("cli-agent-plan.json")
    advisor_exchange = _load_fixture("advisor-exchange.json")
    dataset_spec = _load_fixture("dataset-spec.json")
    generation_manifest = _load_fixture("generation-manifest.json")
    mcp_plan = _load_fixture("mcp-plan.json")
    mcp_generate = _load_fixture("mcp-generate.json")
    generator_tools = _load_fixture_list("mcp-generator-tools.json")
    public_python_api = _load_fixture("public-python-api.json")
    trino_tools = _load_fixture_list("mcp-trino-tools.json")
    artifact_layout = _load_fixture("artifact-layout.json")
    boundary_compatibility = _load_fixture("boundary-compatibility.json")
    validation_report = _load_fixture("validation-report.json")
    contract_catalog = _load_fixture("contract-catalog.json")

    AgentResult.model_validate(cli_plan)
    AdvisorExchange.model_validate(advisor_exchange)
    DatasetSpec.model_validate(dataset_spec)
    GenerationManifest.model_validate(generation_manifest)
    DatasetValidationReport.model_validate(validation_report)

    assert mcp_plan["approval_required"] is True
    assert mcp_generate["source_rows_copied"] is False
    assert mcp_generate["synthetic"] is True
    assert "rows" not in mcp_plan
    assert "rows" not in mcp_generate
    serialized = json.dumps(
        {
            "cli": cli_plan,
            "advisor": advisor_exchange,
            "boundary": boundary_compatibility,
            "mcp_plan": mcp_plan,
            "mcp_generate": mcp_generate,
        }
    )
    assert "@" not in serialized
    assert "sk-" not in serialized
    normalized_dependencies = generation_manifest["reproducibility"][
        "normalized_dependencies"
    ]
    assert {"faker", "pydantic", "pyyaml"} <= set(normalized_dependencies)
    assert public_python_api["exports"] == sorted(test_data_agent.__all__)
    assert all(hasattr(test_data_agent, name) for name in public_python_api["exports"])
    assert artifact_layout["files"] == [
        "dataset_spec.yaml",
        "generation_manifest.json",
        "orders.json",
        "validation_report.json",
    ]
    assert {tool["name"] for tool in generator_tools} == {
        "approve_dataset_plan",
        "export_dataset",
        "generate_dataset",
        "infer_dataset_spec",
        "inspect_dataset_plan",
        "plan_dataset",
        "plan_trino_dataset",
        "profile_csv",
        "recover_dataset_plan",
        "validate_dataset",
    }
    trino_tool_names = {tool["name"] for tool in trino_tools}
    assert "run_safe_select" not in trino_tool_names
    assert "sample_rows_masked" not in trino_tool_names
    for tool in [*generator_tools, *trino_tools]:
        assert tool["input_schema"]["type"] == "object"
        assert tool["output_schema"] is not None
    assert contract_catalog["schema_version"] == "1.0"
    assert boundary_compatibility["cli_error"] == {
        "exit_code": 2,
        "payload": {
            "error": {
                "code": "invalid_input",
                "command": "test-data-agent agent-plan",
                "exit_code": 2,
                "help": None,
                "message": (
                    "agent-plan detected a DatasetSpec; use "
                    "'test-data-agent generate' for reviewed specs"
                ),
                "retryable": False,
            },
            "ok": False,
            "schema_version": "1.0",
        },
    }
    assert boundary_compatibility["safety"] == {
        "generated_output": {
            "source_rows_copied": False,
            "synthetic": True,
        },
        "unsafe_sql": {
            "exception": "SqlSafetyError",
            "message": "DDL, DML, and executable statements are not allowed",
        },
    }
    assert boundary_compatibility["wrappers"]["cli_entry_points"] == [
        "build_parser",
        "main",
    ]


def test_contract_catalog_versions_every_public_fixture() -> None:
    catalog = _load_fixture("contract-catalog.json")
    registered = catalog["contracts"]
    expected = set(CONTRACT_FIXTURE_NAMES) - {"contract-catalog.json"}

    assert set(registered) == expected
    for contract in registered.values():
        assert contract["version"] == "1.0"
        assert contract["change_rule"] in {
            "additive_only",
            "schema_versioned",
        }


def _load_fixture(name: str) -> dict[str, Any]:
    return json.loads(CONTRACT_FIXTURE_DIR.joinpath(name).read_text(encoding="utf-8"))


def _load_fixture_list(name: str) -> list[dict[str, Any]]:
    return json.loads(CONTRACT_FIXTURE_DIR.joinpath(name).read_text(encoding="utf-8"))
