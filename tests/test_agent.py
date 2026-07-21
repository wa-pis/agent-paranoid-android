import csv
import json
from pathlib import Path

import test_data_agent
from test_data_agent.agent import AgentRequest, AgentSourceType, approve_agent_workspace, plan_agent_request
from test_data_agent.core.settings import OutputFormat


FIXTURE_CUSTOMERS = Path("tests/fixtures/customers.csv")
FIXTURE_EXAMPLE_DATASET = Path("tests/fixtures/example_dataset")


def test_package_root_exposes_agent_api() -> None:
    assert test_data_agent.AgentRequest is AgentRequest
    assert test_data_agent.AgentSourceType is AgentSourceType
    assert test_data_agent.plan_agent_request is plan_agent_request
    assert test_data_agent.approve_agent_workspace is approve_agent_workspace


def test_agent_plan_stops_before_generation_for_csv_folder(tmp_path) -> None:
    workspace = tmp_path / "agent"

    result = plan_agent_request(
        AgentRequest(
            source_type=AgentSourceType.CSV_FOLDER,
            source_path=FIXTURE_EXAMPLE_DATASET,
            workspace=workspace,
            count=6,
            seed=12345,
            output_format=OutputFormat.CSV,
        )
    )

    profile_text = (workspace / "profile.json").read_text()
    plan = json.loads((workspace / "agent_plan.json").read_text())
    request = json.loads((workspace / "agent_request.json").read_text())

    assert result.phase == "awaiting_approval"
    assert (workspace / "dataset_spec.yaml").is_file()
    assert not (workspace / "generated").exists()
    assert "alice@example.com" not in profile_text
    assert plan["approval_required"] is True
    assert plan["steps"][2]["name"] == "approval"
    assert plan["steps"][2]["status"] == "pending"
    assert request["source_type"] == "csv_folder"
    assert request["seed"] == 12345


def test_agent_approve_generates_safe_csv_folder_bundle(tmp_path) -> None:
    workspace = tmp_path / "agent"
    plan_agent_request(
        AgentRequest(
            source_type=AgentSourceType.CSV_FOLDER,
            source_path=FIXTURE_EXAMPLE_DATASET,
            workspace=workspace,
            count=5,
            seed=77,
            output_format=OutputFormat.CSV,
        )
    )

    result = approve_agent_workspace(workspace)

    manifest = json.loads((workspace / "generated" / "generation_manifest.json").read_text())
    report = json.loads((workspace / "generated" / "validation_report.json").read_text())
    generated_rows = load_csv_folder(workspace / "generated")
    source_rows = load_csv_folder(FIXTURE_EXAMPLE_DATASET)

    assert result.phase == "completed"
    assert result.summary["row_counts"] == {"customers": 5, "orders": 5}
    assert result.summary["validation_valid"] is True
    assert manifest["synthetic"] is True
    assert manifest["source_rows_copied"] is False
    assert manifest["seed"] == 77
    assert manifest["row_counts"] == {"customers": 5, "orders": 5}
    assert report["valid"] is True
    assert not copied_rows(generated_rows, source_rows)


def test_agent_approve_generates_safe_single_csv_bundle(tmp_path) -> None:
    workspace = tmp_path / "agent_csv"
    plan_agent_request(
        AgentRequest(
            source_type=AgentSourceType.CSV,
            source_path=FIXTURE_CUSTOMERS,
            workspace=workspace,
            count=4,
            seed=19,
            output_format=OutputFormat.CSV,
            table_name="customers_agent",
        )
    )

    result = approve_agent_workspace(workspace)

    rows = list(csv.DictReader((workspace / "generated" / "customers_agent.csv").open()))
    source_rows = list(csv.DictReader(FIXTURE_CUSTOMERS.open()))
    profile_text = (workspace / "profile.json").read_text()

    assert result.summary["row_counts"] == {"customers_agent": 4}
    assert len(rows) == 4
    assert "alice@example.com" not in profile_text
    assert {tuple(row.items()) for row in rows}.isdisjoint({tuple(row.items()) for row in source_rows})


def load_csv_folder(folder: Path) -> dict[str, list[dict[str, str]]]:
    rows = {}
    for path in folder.glob("*.csv"):
        with path.open(newline="") as handle:
            rows[path.stem] = list(csv.DictReader(handle))
    return rows


def copied_rows(generated: dict[str, list[dict[str, str]]], source: dict[str, list[dict[str, str]]]) -> bool:
    for table, rows in generated.items():
        generated_normalized = {tuple(row.items()) for row in rows}
        source_normalized = {tuple(row.items()) for row in source.get(table, [])}
        if generated_normalized & source_normalized:
            return True
    return False
