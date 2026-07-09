import csv
import json
from pathlib import Path

from test_data_agent.core.dataset import DatasetProfile
from test_data_agent.core.entity import EntityProfile
from test_data_agent.core.field import FieldProfile
from test_data_agent.core.settings import OutputFormat
from test_data_agent.io.workflows import (
    infer_dataset_spec_artifact,
    generate_dataset_from_csv_artifacts,
    generate_dataset_from_profile_artifacts,
    write_csv_profile_artifact,
)


def test_generate_dataset_from_profile_artifacts_writes_outputs_and_uses_seed(tmp_path) -> None:
    profile = DatasetProfile(
        source_type="json_profile",
        entities=[
            EntityProfile(
                name="orders",
                row_count=2,
                primary_key_candidates=["order_id"],
                fields=[
                    FieldProfile(
                        name="order_id",
                        data_type="integer",
                        is_identifier=True,
                    ),
                    FieldProfile(
                        name="status",
                        data_type="string",
                        distribution={
                            "kind": "categorical",
                            "categories": [
                                {"value": "new", "count": 2},
                                {"value": "shipped", "count": 1},
                            ],
                        },
                    ),
                ],
            )
        ],
    )
    output_path = tmp_path / "generated" / "orders.json"
    applied: list[tuple[list[dict[str, object]], int]] = []

    def capture_business_rules(rows_by_entity: dict[str, list[dict[str, object]]], seed: int) -> None:
        applied.append((rows_by_entity["orders"], seed))
        return None

    report, business_report = generate_dataset_from_profile_artifacts(
        profile,
        count=3,
        seed=41,
        output_path=output_path,
        output_format=None,
        business_rules_applier=capture_business_rules,
    )

    rows = json.loads(output_path.read_text())
    profile_artifact = json.loads((output_path.parent / "profile.json").read_text())
    spec_artifact = json.loads((output_path.parent / "generation_spec.json").read_text())
    validation_artifact = json.loads((output_path.parent / "validation_report.json").read_text())

    assert report.valid is True
    assert business_report is None
    assert len(rows) == 3
    assert profile_artifact["source_type"] == "json_profile"
    assert spec_artifact["generation_settings"]["seed"] == 41
    assert spec_artifact["entities"][0]["row_count"] == 3
    assert validation_artifact["valid"] is True
    assert applied and applied[0][1] == 41
    assert applied[0][0] == rows


def test_generate_dataset_from_csv_artifacts_writes_csv_profile_and_generation_artifacts(tmp_path) -> None:
    input_path = tmp_path / "orders.csv"
    output_path = tmp_path / "generated" / "orders.csv"
    input_path.write_text("order_id,status\n1,new\n2,shipped\n")
    applied: list[tuple[list[dict[str, str]], int]] = []

    def capture_business_rules(rows_by_entity: dict[str, list[dict[str, str]]], seed: int) -> None:
        applied.append((rows_by_entity["orders"], seed))
        return None

    report, business_report = generate_dataset_from_csv_artifacts(
        input_path,
        count=4,
        seed=23,
        output_path=output_path,
        output_format=OutputFormat.CSV,
        table_name="orders",
        business_rules_applier=capture_business_rules,
    )

    with output_path.open() as handle:
        rows = list(csv.DictReader(handle))
    profile_artifact = json.loads((output_path.parent / "csv_profile.json").read_text())
    spec_artifact = json.loads((output_path.parent / "generation_spec.json").read_text())
    validation_artifact = json.loads((output_path.parent / "validation_report.json").read_text())

    assert report.valid is True
    assert business_report is None
    assert len(rows) == 4
    assert profile_artifact["source_type"] == "csv"
    assert spec_artifact["generation_settings"]["seed"] == 23
    assert spec_artifact["generation_settings"]["output_format"] == "csv"
    assert validation_artifact["valid"] is True
    assert applied and applied[0][1] == 23
    assert [{key: str(value) for key, value in row.items()} for row in applied[0][0]] == rows


def test_generate_dataset_from_csv_artifacts_uses_shared_profile_builder_for_mode_settings(tmp_path) -> None:
    input_path = tmp_path / "orders.csv"
    output_path = tmp_path / "generated" / "orders.json"
    input_path.write_text("order_id,status\n1,new\n2,shipped\n")

    report, _ = generate_dataset_from_csv_artifacts(
        input_path,
        count=5,
        seed=31,
        output_path=output_path,
        output_format=OutputFormat.JSON,
        table_name="orders",
        mode="mixed",
        invalid_ratio=0.4,
    )

    spec_artifact = json.loads((output_path.parent / "generation_spec.json").read_text())
    validation_artifact = json.loads((output_path.parent / "validation_report.json").read_text())

    assert report.valid is False
    assert spec_artifact["generation_settings"]["seed"] == 31
    assert spec_artifact["generation_settings"]["output_format"] == "json"
    assert spec_artifact["generation_settings"]["mode"] == "mixed"
    assert spec_artifact["generation_settings"]["invalid_ratio"] == 0.4
    assert spec_artifact["entities"][0]["row_count"] == 5
    assert validation_artifact["valid"] is False


def test_infer_dataset_spec_artifact_writes_dataset_spec_yaml(tmp_path) -> None:
    profile = DatasetProfile(
        source_type="json_profile",
        entities=[
            EntityProfile(
                name="orders",
                row_count=2,
                fields=[
                    FieldProfile(name="order_id", data_type="integer", is_identifier=True),
                    FieldProfile(name="status", data_type="string"),
                ],
            )
        ],
    )
    output_path = tmp_path / "dataset_spec.yaml"

    spec = infer_dataset_spec_artifact(profile, output_path=output_path, count=4)

    written = output_path.read_text()

    assert spec.entities[0].row_count == 4
    assert "generation_settings:" in written
    assert "row_count: 4" in written


def test_write_csv_profile_artifact_writes_dataset_profile_json(tmp_path) -> None:
    input_path = tmp_path / "orders.csv"
    output_path = tmp_path / "profile.json"
    input_path.write_text("order_id,status\n1,new\n2,shipped\n")

    profile = write_csv_profile_artifact(input_path, output_path=output_path, table_name="orders")

    written = json.loads(output_path.read_text())

    assert profile.entities[0].name == "orders"
    assert written["source_type"] == "csv"
    assert written["entities"][0]["name"] == "orders"
