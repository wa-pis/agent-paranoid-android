import csv
import errno
import hashlib
import json
from pathlib import Path

import pytest

from test_data_agent.core.dataset import DatasetProfile, DatasetSpec
from test_data_agent.core.entity import EntityProfile, EntitySpec
from test_data_agent.core.field import FieldProfile, FieldSpec
from test_data_agent.core.limits import GenerationLimitError
from test_data_agent.core.settings import OutputFormat
from test_data_agent.io.artifacts import write_json_artifact_atomic
from test_data_agent.io.workflows import (
    commit_temp_output_folder,
    generate_dataset_bundle,
    generate_dataset_review_artifacts,
    infer_dataset_spec_artifact,
    generate_dataset_from_csv_artifacts,
    generate_dataset_from_profile_artifacts,
    write_csv_profile_artifact,
)
from test_data_agent.safety import SourceRowReuseError


def test_atomic_json_artifact_does_not_follow_target_symlink(tmp_path) -> None:
    outside = tmp_path / "outside.json"
    outside.write_text("unchanged")
    output = tmp_path / "result.json"
    output.symlink_to(outside)

    with pytest.raises(ValueError, match="regular file"):
        write_json_artifact_atomic({"safe": True}, output)

    assert outside.read_text() == "unchanged"
    assert output.is_symlink()


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
    spec_artifact = json.loads((output_path.parent / "dataset_spec.json").read_text())
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
    evidence = manifest["reproducibility"]
    assert evidence["guarantee"] == "same_environment_logical"
    assert evidence["byte_identical_across_versions"] is False
    assert evidence["locale"] == "en_US"
    assert evidence["serializer"] == "python-stdlib-json"
    assert evidence["generator_algorithm_version"] == manifest["package_version"]
    normalized_dependencies = evidence["normalized_dependencies"]
    assert {"faker", "pydantic", "pyyaml"} <= set(normalized_dependencies)
    normalized_payload = json.dumps(
        normalized_dependencies,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    assert evidence["normalized_dependencies_sha256"] == hashlib.sha256(
        normalized_payload
    ).hexdigest()
    assert evidence["output_sha256"]["orders.json"] == hashlib.sha256(
        output_path.read_bytes()
    ).hexdigest()
    assert "generation_manifest.json" not in evidence["output_sha256"]
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
    spec_artifact = json.loads((output_path.parent / "dataset_spec.json").read_text())
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

    spec_artifact = json.loads((output_path.parent / "dataset_spec.json").read_text())
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
        rules_sha256 = "a" * 64
        rule_count = 2

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
        "rules_sha256": "a" * 64,
        "rule_count": 2,
        "rule_pass_count": 0,
        "rule_fail_count": 0,
        "valid": False,
        "errors_truncated": False,
        "expected_violation_count": 0,
        "observed_violation_count": 0,
        "unexpected_violation_count": 0,
        "missing_expected_violation_count": 0,
        "expectations_met": True,
    }
    assert manifest["effective_rules"] == {
        "spec_sha256": manifest["spec_sha256"],
        "generation_mode": "valid",
        "invalid_ratio": 0.0,
        "locale": "en_US",
        "validation_settings": {
            "validate_schema": True,
            "validate_relationships": True,
            "validate_constraints": True,
            "validate_privacy": True,
            "fail_fast": False,
        },
        "relationship_count": 0,
        "constraint_count": 0,
        "distributed_field_count": 0,
        "business_rules_sha256": "a" * 64,
        "business_rule_count": 2,
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


@pytest.mark.parametrize("workflow", ["folder", "review", "single"])
def test_staged_workflows_remove_temp_output_when_time_budget_expires(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    workflow: str,
) -> None:
    class ExportDeadline:
        def check(self, stage: str) -> None:
            deadline_stage = (
                "artifact publication" if workflow == "single" else "dataset export"
            )
            if stage == deadline_stage:
                raise GenerationLimitError("generation deadline reached")

    monkeypatch.setattr(
        "test_data_agent.io.workflows.prepare_generation_budget",
        lambda spec, output_path: ExportDeadline(),
    )
    profile = DatasetProfile(
        source_type="json_profile",
        entities=[
            EntityProfile(
                name="orders",
                row_count=1,
                fields=[FieldProfile(name="status", data_type="string")],
            )
        ],
    )
    spec = infer_dataset_spec_artifact(
        profile,
        output_path=tmp_path / "dataset_spec.yaml",
        count=1,
    )

    if workflow == "folder":
        output = tmp_path / "generated"
        temporary_parent = tmp_path
        temporary_pattern = ".generated.*"

        def operation():
            return generate_dataset_bundle(spec, output_folder=output)

    elif workflow == "review":
        output = tmp_path / "review"
        temporary_parent = tmp_path
        temporary_pattern = ".review.*"

        def operation():
            return generate_dataset_review_artifacts(
                profile,
                spec,
                output_folder=output,
                output_format=OutputFormat.JSON,
                seed=19,
            )

    else:
        output = tmp_path / "single" / "orders.json"
        temporary_parent = output.parent
        temporary_pattern = ".orders.*"

        def operation():
            return generate_dataset_from_profile_artifacts(
                profile,
                count=1,
                seed=19,
                output_path=output,
                output_format=OutputFormat.JSON,
            )

    with pytest.raises(GenerationLimitError, match="deadline"):
        operation()

    assert not output.exists()
    assert not list(temporary_parent.glob(temporary_pattern))


def test_generate_dataset_bundle_removes_staging_on_cancellation(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    spec = DatasetSpec(
        entities=[
            EntitySpec(
                name="orders",
                row_count=1,
                fields=[FieldSpec(name="status", data_type="string")],
            )
        ]
    )
    monkeypatch.setattr(
        "test_data_agent.io.workflows.write_dataset_rows",
        lambda *args, **kwargs: (_ for _ in ()).throw(KeyboardInterrupt()),
    )

    with pytest.raises(KeyboardInterrupt):
        generate_dataset_bundle(spec, output_folder=tmp_path / "generated")

    assert not (tmp_path / "generated").exists()
    assert not list(tmp_path.glob(".generated.*"))


def test_review_bundle_removes_staging_on_cancellation(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    profile = DatasetProfile(
        source_type="json_profile",
        entities=[
            EntityProfile(
                name="orders",
                row_count=1,
                fields=[FieldProfile(name="status", data_type="string")],
            )
        ],
    )
    spec = infer_dataset_spec_artifact(
        profile,
        output_path=tmp_path / "dataset_spec.yaml",
        count=1,
    )
    monkeypatch.setattr(
        "test_data_agent.io.workflows.write_dataset_rows",
        lambda *args, **kwargs: (_ for _ in ()).throw(KeyboardInterrupt()),
    )

    with pytest.raises(KeyboardInterrupt):
        generate_dataset_review_artifacts(
            profile,
            spec,
            output_folder=tmp_path / "review",
            output_format=OutputFormat.JSON,
            seed=19,
        )

    assert not (tmp_path / "review").exists()
    assert not list(tmp_path.glob(".review.*"))


def test_single_entity_bundle_removes_staging_on_cancellation(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    profile = DatasetProfile(
        source_type="json_profile",
        entities=[
            EntityProfile(
                name="orders",
                row_count=1,
                fields=[FieldProfile(name="status", data_type="string")],
            )
        ],
    )
    output_path = tmp_path / "generated" / "orders.json"
    monkeypatch.setattr(
        "test_data_agent.io.workflows.write_single_entity_rows",
        lambda *args, **kwargs: (_ for _ in ()).throw(KeyboardInterrupt()),
    )

    with pytest.raises(KeyboardInterrupt):
        generate_dataset_from_profile_artifacts(
            profile,
            count=1,
            seed=19,
            output_path=output_path,
            output_format=OutputFormat.JSON,
        )

    assert not output_path.exists()
    assert not list(output_path.parent.glob(".orders.*"))


@pytest.mark.parametrize("workflow", ["folder", "review", "single"])
def test_staged_workflows_remove_partial_output_on_disk_exhaustion(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    workflow: str,
) -> None:
    profile = DatasetProfile(
        source_type="json_profile",
        entities=[
            EntityProfile(
                name="orders",
                row_count=1,
                fields=[FieldProfile(name="status", data_type="string")],
            )
        ],
    )
    spec = infer_dataset_spec_artifact(
        profile,
        output_path=tmp_path / "dataset_spec.yaml",
        count=1,
    )

    def exhaust_folder(rows, output_format, output_folder: Path) -> None:
        (output_folder / "partial.tmp").write_text("incomplete")
        raise OSError(errno.ENOSPC, "No space left on device")

    def exhaust_single(rows, output_format, output_path: Path) -> None:
        output_path.write_text("incomplete")
        raise OSError(errno.ENOSPC, "No space left on device")

    if workflow == "folder":
        output = tmp_path / "generated"
        temporary_parent = tmp_path
        temporary_pattern = ".generated.*"
        monkeypatch.setattr(
            "test_data_agent.io.workflows.write_dataset_rows",
            exhaust_folder,
        )
        def operation():
            return generate_dataset_bundle(spec, output_folder=output)
    elif workflow == "review":
        output = tmp_path / "review"
        temporary_parent = tmp_path
        temporary_pattern = ".review.*"
        monkeypatch.setattr(
            "test_data_agent.io.workflows.write_dataset_rows",
            exhaust_folder,
        )
        def operation():
            return generate_dataset_review_artifacts(
                profile,
                spec,
                output_folder=output,
                output_format=OutputFormat.JSON,
                seed=19,
            )
    else:
        output = tmp_path / "single" / "orders.json"
        temporary_parent = output.parent
        temporary_pattern = ".orders.*"
        monkeypatch.setattr(
            "test_data_agent.io.workflows.write_single_entity_rows",
            exhaust_single,
        )
        def operation():
            return generate_dataset_from_profile_artifacts(
                profile,
                count=1,
                seed=19,
                output_path=output,
                output_format=OutputFormat.JSON,
            )

    with pytest.raises(OSError, match="No space left on device") as raised:
        operation()

    assert raised.value.errno == errno.ENOSPC
    assert not output.exists()
    assert not list(temporary_parent.glob(temporary_pattern))


@pytest.mark.parametrize("workflow", ["folder", "review"])
def test_folder_publication_rolls_back_interruption_after_atomic_rename(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    workflow: str,
) -> None:
    profile = DatasetProfile(
        source_type="json_profile",
        entities=[
            EntityProfile(
                name="orders",
                row_count=1,
                fields=[FieldProfile(name="status", data_type="string")],
            )
        ],
    )
    spec = infer_dataset_spec_artifact(
        profile,
        output_path=tmp_path / "dataset_spec.yaml",
        count=1,
    )
    def interrupt_after_rename(temp_folder: Path, output_folder: Path) -> None:
        commit_temp_output_folder(temp_folder, output_folder)
        raise RuntimeError("publication interrupted")

    monkeypatch.setattr(
        "test_data_agent.io.workflows.commit_temp_output_folder",
        interrupt_after_rename,
    )
    output = tmp_path / workflow

    with pytest.raises(RuntimeError, match="publication interrupted"):
        if workflow == "folder":
            generate_dataset_bundle(spec, output_folder=output)
        else:
            generate_dataset_review_artifacts(
                profile,
                spec,
                output_folder=output,
                output_format=OutputFormat.JSON,
                seed=19,
            )

    assert not output.exists()
    assert not list(tmp_path.glob(f".{workflow}.*"))


def test_single_entity_commit_restores_existing_files_when_interrupted(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    profile = DatasetProfile(
        source_type="json_profile",
        entities=[
            EntityProfile(
                name="orders",
                row_count=1,
                fields=[FieldProfile(name="status", data_type="string")],
            )
        ],
    )
    output_folder = tmp_path / "single"
    output_folder.mkdir()
    existing_profile = output_folder / "profile.json"
    existing_profile.write_text("previous profile")
    unrelated = output_folder / "keep.txt"
    unrelated.write_text("keep")
    output_path = output_folder / "orders.json"
    from test_data_agent.io.path_policy import replace_path as original_replace

    def interrupt_profile_move(path: Path, target: Path) -> None:
        original_replace(path, target)
        if (
            path.parent.name.startswith(".orders.")
            and path.name == "profile.json"
            and Path(target).parent == output_folder
        ):
            raise RuntimeError("single publication interrupted")

    monkeypatch.setattr(
        "test_data_agent.io.workflows.replace_path",
        interrupt_profile_move,
    )

    with pytest.raises(RuntimeError, match="single publication interrupted"):
        generate_dataset_from_profile_artifacts(
            profile,
            count=1,
            seed=19,
            output_path=output_path,
            output_format=OutputFormat.JSON,
        )

    assert not output_path.exists()
    assert existing_profile.read_text() == "previous profile"
    assert unrelated.read_text() == "keep"
    assert not list(output_folder.glob(".orders.*"))


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
