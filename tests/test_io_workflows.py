import csv
import json
import test_data_agent.io as io_package
from pathlib import Path

import pytest

from test_data_agent.core.dataset import DatasetProfile, DatasetSpec
from test_data_agent.core.entity import EntityProfile, EntitySpec
from test_data_agent.core.field import FieldProfile, FieldSpec
from test_data_agent.core.limits import GenerationLimitError
from test_data_agent.core.settings import OutputFormat
from test_data_agent.io.workflows import (
    generate_dataset_bundle,
    generate_dataset_review_artifacts,
    infer_dataset_spec_artifact,
    generate_dataset_from_csv_artifacts,
    generate_dataset_from_profile_artifacts,
    write_csv_profile_artifact,
)
from test_data_agent.safety import SourceRowReuseError


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
    manifest = json.loads((output_path.parent / "generation_manifest.json").read_text())

    assert report.valid is True
    assert business_report is None
    assert len(rows) == 3
    assert profile_artifact["source_type"] == "json_profile"
    assert spec_artifact["generation_settings"]["seed"] == 41
    assert spec_artifact["entities"][0]["row_count"] == 3
    assert validation_artifact["valid"] is True
    assert manifest["source_rows_copied"] is False
    assert manifest["seed"] == 41
    assert applied and applied[0][1] == 41
    assert applied[0][0] == rows


def test_generate_dataset_from_csv_artifacts_writes_csv_profile_and_generation_artifacts(tmp_path) -> None:
    input_path = tmp_path / "orders.csv"
    output_path = tmp_path / "generated" / "orders.csv"
    input_path.write_text("order_id,status\n101,new\n102,shipped\n")
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
    manifest = json.loads((output_path.parent / "generation_manifest.json").read_text())

    assert report.valid is True
    assert business_report is None
    assert len(rows) == 4
    assert profile_artifact["source_type"] == "csv"
    assert spec_artifact["generation_settings"]["seed"] == 23
    assert spec_artifact["generation_settings"]["output_format"] == "csv"
    assert validation_artifact["valid"] is True
    assert manifest["source_rows_copied"] is False
    assert manifest["seed"] == 23
    assert applied and applied[0][1] == 23
    assert [{key: str(value) for key, value in row.items()} for row in applied[0][0]] == rows


def test_generate_dataset_from_csv_artifacts_uses_shared_profile_builder_for_mode_settings(tmp_path) -> None:
    input_path = tmp_path / "orders.csv"
    output_path = tmp_path / "generated" / "orders.json"
    input_path.write_text("order_id,status\n101,new\n102,shipped\n")

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


def test_generate_dataset_from_csv_stops_before_write_when_source_row_is_reused(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    input_path = tmp_path / "orders.csv"
    output_path = tmp_path / "generated" / "orders.csv"
    input_path.write_text("order_id,status\n1,new\n")
    monkeypatch.setattr(
        "test_data_agent.io.workflows.generate_dataset",
        lambda spec, seed, budget: {"orders": [{"order_id": "1", "status": "new"}]},
    )

    with pytest.raises(SourceRowReuseError):
        generate_dataset_from_csv_artifacts(
            input_path,
            count=1,
            seed=0,
            output_path=output_path,
            output_format=OutputFormat.CSV,
            table_name="orders",
        )

    assert not output_path.exists()


def test_generate_dataset_from_csv_does_not_publish_rows_when_artifact_write_fails(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    input_path = tmp_path / "orders.csv"
    output_path = tmp_path / "generated" / "orders.csv"
    input_path.write_text("order_id,status\n101,new\n102,shipped\n")

    def fail_artifact_write(*args, **kwargs) -> None:
        raise RuntimeError("artifact write failed")

    monkeypatch.setattr(
        "test_data_agent.io.workflows.write_dataset_generation_artifacts",
        fail_artifact_write,
    )

    with pytest.raises(RuntimeError, match="artifact write failed"):
        generate_dataset_from_csv_artifacts(
            input_path,
            count=2,
            seed=0,
            output_path=output_path,
            output_format=OutputFormat.CSV,
            table_name="orders",
        )

    assert not output_path.exists()
    assert not (output_path.parent / "generation_manifest.json").exists()
    assert list(output_path.parent.iterdir()) == []


def test_generate_dataset_from_csv_rejects_source_output_collision(tmp_path: Path) -> None:
    input_path = tmp_path / "orders.csv"
    input_path.write_text("order_id,status\n1,new\n")

    with pytest.raises(ValueError, match="different"):
        generate_dataset_from_csv_artifacts(
            input_path,
            count=1,
            seed=0,
            output_path=input_path,
            output_format=OutputFormat.CSV,
        )


def test_generation_manifest_includes_business_validation_status(tmp_path: Path) -> None:
    spec = DatasetSpec(
        entities=[
            EntitySpec(
                name="orders",
                row_count=1,
                fields=[FieldSpec(name="status", data_type="string")],
            )
        ]
    )

    class InvalidBusinessReport:
        valid = False

        def model_dump_json(self, indent: int) -> str:
            return '{"valid": false}'

    result = generate_dataset_bundle(
        spec,
        output_folder=tmp_path / "generated",
        business_rules_applier=lambda rows, seed, spec: InvalidBusinessReport(),
    )

    manifest = json.loads((tmp_path / "generated" / "generation_manifest.json").read_text())
    assert result.business_validation is not None
    assert manifest["validation_valid"] is False
    assert manifest["business_validation"] == {
        "rules_sha256": None,
        "rule_count": 0,
        "rule_pass_count": 0,
        "rule_fail_count": 0,
        "valid": False,
        "errors_truncated": False,
    }


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


def test_infer_dataset_spec_artifact_writes_json_for_json_suffix(tmp_path) -> None:
    profile = DatasetProfile(
        source_type="json_profile",
        entities=[
            EntityProfile(
                name="orders",
                row_count=2,
                fields=[FieldProfile(name="order_id", data_type="integer", is_identifier=True)],
            )
        ],
    )
    output_path = tmp_path / "dataset_spec.json"

    infer_dataset_spec_artifact(profile, output_path=output_path, count=3)

    payload = json.loads(output_path.read_text())
    assert payload["schema_version"] == "1.0"
    assert payload["entities"][0]["row_count"] == 3


def test_write_csv_profile_artifact_writes_dataset_profile_json(tmp_path) -> None:
    input_path = tmp_path / "orders.csv"
    output_path = tmp_path / "profile.json"
    input_path.write_text("order_id,status\n1,new\n2,shipped\n")

    profile = write_csv_profile_artifact(input_path, output_path=output_path, table_name="orders")

    written = json.loads(output_path.read_text())

    assert profile.entities[0].name == "orders"
    assert written["source_type"] == "csv"
    assert written["entities"][0]["name"] == "orders"


def test_generate_dataset_review_artifacts_writes_review_bundle(tmp_path) -> None:
    profile = DatasetProfile(
        source_type="json_profile",
        entities=[
            EntityProfile(
                name="orders",
                row_count=2,
                primary_key_candidates=["order_id"],
                fields=[
                    FieldProfile(name="order_id", data_type="integer", is_identifier=True),
                    FieldProfile(name="status", data_type="string"),
                ],
            )
        ],
    )
    spec = infer_dataset_spec_artifact(profile, output_path=tmp_path / "dataset_spec.yaml", count=3)
    output_folder = tmp_path / "review"

    exit_code = generate_dataset_review_artifacts(
        profile,
        spec,
        output_folder=output_folder,
        output_format=OutputFormat.JSON,
        seed=19,
    )

    assert exit_code == 0
    assert json.loads((output_folder / "orders.json").read_text())
    assert json.loads((output_folder / "profile.json").read_text())["entities"][0]["name"] == "orders"
    assert "generation_settings:" in (output_folder / "dataset_spec.yaml").read_text()
    assert json.loads((output_folder / "validation_report.json").read_text())["valid"] is True


def test_generate_dataset_bundle_does_not_leave_partial_output_on_validation_error(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
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
    spec = infer_dataset_spec_artifact(profile, output_path=tmp_path / "dataset_spec.yaml", count=2)

    def fail_validation(rows_by_entity, spec):
        raise RuntimeError("validation failed")

    monkeypatch.setattr("test_data_agent.io.workflows.validate_dataset", fail_validation)

    with pytest.raises(RuntimeError, match="validation failed"):
        generate_dataset_bundle(
            spec,
            output_folder=tmp_path / "generated",
            output_format=OutputFormat.JSON,
            seed=11,
        )

    assert not (tmp_path / "generated").exists()
    assert not list(tmp_path.glob(".generated.*"))


def test_generate_dataset_bundle_rejects_estimated_oversized_output(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setenv("TEST_DATA_AGENT_MAX_OUTPUT_BYTES", "100")
    monkeypatch.setenv("TEST_DATA_AGENT_MIN_FREE_DISK_BYTES", "1")
    spec = DatasetSpec(
        entities=[
            EntitySpec(
                name="orders",
                row_count=1,
                fields=[FieldSpec(name="status", data_type="string")],
            )
        ]
    )

    with pytest.raises(GenerationLimitError, match="estimated generated data"):
        generate_dataset_bundle(spec, output_folder=tmp_path / "generated")

    assert not (tmp_path / "generated").exists()
    assert not list(tmp_path.glob(".generated.*"))


def test_generate_dataset_bundle_removes_temp_output_when_time_budget_expires(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    class ExportDeadline:
        def check(self, stage: str) -> None:
            if stage == "dataset export":
                raise GenerationLimitError("generation deadline reached")

    monkeypatch.setattr(
        "test_data_agent.io.workflows.prepare_generation_budget",
        lambda spec, output_path: ExportDeadline(),
    )
    spec = DatasetSpec(
        entities=[
            EntitySpec(
                name="orders",
                row_count=1,
                fields=[FieldSpec(name="status", data_type="string")],
            )
        ]
    )

    with pytest.raises(GenerationLimitError, match="deadline"):
        generate_dataset_bundle(spec, output_folder=tmp_path / "generated")

    assert not (tmp_path / "generated").exists()
    assert not list(tmp_path.glob(".generated.*"))


def test_generate_dataset_from_profile_artifacts_enforces_configured_row_limit(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setenv("TEST_DATA_AGENT_MAX_GENERATION_COUNT", "2")
    profile = DatasetProfile(
        source_type="json_profile",
        entities=[
            EntityProfile(
                name="orders",
                row_count=10,
                fields=[FieldProfile(name="order_id", data_type="integer", is_identifier=True)],
            )
        ],
    )

    with pytest.raises(ValueError, match="entity row_count must be <= 2"):
        generate_dataset_from_profile_artifacts(
            profile,
            count=3,
            seed=11,
            output_path=tmp_path / "orders.json",
            output_format=OutputFormat.JSON,
        )


def test_generate_dataset_review_artifacts_enforces_configured_row_limit(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setenv("TEST_DATA_AGENT_MAX_GENERATION_COUNT", "2")
    profile = DatasetProfile(
        source_type="json_profile",
        entities=[
            EntityProfile(
                name="orders",
                row_count=3,
                fields=[FieldProfile(name="order_id", data_type="integer", is_identifier=True)],
            )
        ],
    )
    spec = infer_dataset_spec_artifact(profile, output_path=tmp_path / "dataset_spec.yaml", count=3)

    with pytest.raises(ValueError, match="entity row_count must be <= 2"):
        generate_dataset_review_artifacts(
            profile,
            spec,
            output_folder=tmp_path / "review",
            output_format=OutputFormat.JSON,
            seed=19,
        )


def test_io_package_keeps_legacy_workflows_out_of_dataset_oriented_exports() -> None:
    assert not hasattr(io_package, "generate_legacy_spec_artifacts")
    assert not hasattr(io_package, "validate_legacy_spec_artifacts")
    assert not hasattr(io_package, "warn_deprecated_generation_spec_compatibility")
    assert not hasattr(io_package, "write_tabular_rows")
