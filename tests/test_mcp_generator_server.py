import csv
import json
from pathlib import Path

import pytest

from test_data_agent.mcp_generator_server import (
    WorkspacePathError,
    export_dataset,
    generate_dataset,
    infer_dataset_spec,
    profile_csv,
    resolve_workspace_path,
    validate_dataset,
)
from test_data_agent.safety import ProfileSafetyError


def configure_workspace(monkeypatch: pytest.MonkeyPatch, root: Path) -> None:
    monkeypatch.setenv("TEST_DATA_AGENT_WORKSPACE_ROOT", str(root))


def write_source_csv(root: Path) -> None:
    (root / "customers.csv").write_text(
        "customer_id,email,status\n"
        "1,alice@example.com,active\n"
        "2,bob@example.com,paused\n"
    )


def test_workspace_paths_reject_escape(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    configure_workspace(monkeypatch, tmp_path)

    with pytest.raises(WorkspacePathError, match="escapes"):
        resolve_workspace_path("../outside.csv")


def test_workspace_paths_reject_symlink_escape(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    workspace = tmp_path / "workspace"
    outside = tmp_path / "outside"
    workspace.mkdir()
    outside.mkdir()
    (workspace / "linked").symlink_to(outside, target_is_directory=True)
    configure_workspace(monkeypatch, workspace)

    with pytest.raises(WorkspacePathError, match="escapes"):
        resolve_workspace_path("linked/output.json")


def test_profile_csv_returns_metadata_only_and_masks_pii(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    configure_workspace(monkeypatch, tmp_path)
    write_source_csv(tmp_path)

    result = profile_csv("customers.csv", "artifacts/profile.json")
    serialized_result = json.dumps(result)
    serialized_profile = (tmp_path / "artifacts" / "profile.json").read_text()

    assert result["entities"][0]["sensitive_field_count"] == 1
    assert "alice@example.com" not in serialized_result
    assert "alice@example.com" not in serialized_profile
    assert '"pattern": "email"' in serialized_profile


def test_infer_generate_validate_and_export_dataset_through_mcp_tools(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    configure_workspace(monkeypatch, tmp_path)
    write_source_csv(tmp_path)
    profile_csv("customers.csv", "artifacts/profile.json")

    inferred = infer_dataset_spec(
        output_path="artifacts/dataset_spec.yaml",
        profile_path="artifacts/profile.json",
        count=4,
    )
    generated = generate_dataset(
        "artifacts/dataset_spec.yaml",
        "generated/csv",
        output_format="csv",
        seed=41,
    )
    validated = validate_dataset(
        "generated/csv/dataset_spec.yaml",
        "generated/csv",
        "generated/csv/validation_manual.json",
    )
    exported = export_dataset(
        "artifacts/dataset_spec.yaml",
        "generated/json",
        output_format="json",
        seed=41,
    )

    with (tmp_path / "generated" / "csv" / "customers.csv").open() as handle:
        csv_rows = list(csv.DictReader(handle))
    json_rows = json.loads((tmp_path / "generated" / "json" / "customers.json").read_text())

    assert inferred["schema_version"] == "1.0"
    assert generated["row_counts"] == {"customers": 4}
    assert generated["validation"]["valid"] is True
    assert validated["validation"]["valid"] is True
    assert exported["output_format"] == "json"
    assert len(csv_rows) == len(json_rows) == 4
    assert csv_rows[0]["customer_id"] == str(json_rows[0]["customer_id"])
    assert csv_rows[0]["email"] == json_rows[0]["email"]
    assert "alice@example.com" not in json.dumps(json_rows)


def test_infer_dataset_spec_rejects_raw_sensitive_profile(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    configure_workspace(monkeypatch, tmp_path)
    (tmp_path / "unsafe_profile.json").write_text(
        json.dumps(
            {
                "source_type": "manual",
                "entities": [
                    {
                        "name": "customers",
                        "row_count": 1,
                        "fields": [
                            {
                                "name": "customer_email",
                                "data_type": "string",
                                "sensitive": True,
                                "distribution": {
                                    "kind": "categorical",
                                    "categories": [{"value": "alice@example.com", "count": 1}],
                                },
                            }
                        ],
                    }
                ],
            }
        )
    )

    with pytest.raises(ProfileSafetyError, match="unsafe distribution"):
        infer_dataset_spec(
            output_path="dataset_spec.yaml",
            profile_path="unsafe_profile.json",
        )


def test_infer_dataset_spec_accepts_inline_safe_trino_profile(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    configure_workspace(monkeypatch, tmp_path)

    result = infer_dataset_spec(
        output_path="dataset_spec.yaml",
        profile_payload={
            "source_type": "trino",
            "table": "orders",
            "row_count": 100,
            "columns": [
                {
                    "name": "order_id",
                    "data_type": "bigint",
                    "approx_distinct_count": 100,
                },
                {
                    "name": "customer_email",
                    "data_type": "varchar",
                    "sensitive": True,
                    "semantic_type": "email",
                    "masked_patterns": [{"pattern": "email", "count": 100}],
                },
            ],
        },
        count=5,
    )

    assert result["operation"] == "infer_dataset_spec"
    assert result["entities"] == [{"name": "orders", "row_count": 5, "field_count": 2}]
    assert "@" not in (tmp_path / "dataset_spec.yaml").read_text()


def test_profile_csv_does_not_overwrite_input(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    configure_workspace(monkeypatch, tmp_path)
    write_source_csv(tmp_path)

    with pytest.raises(WorkspacePathError, match="profile output"):
        profile_csv("customers.csv", "customers.csv")


def test_mcp_tools_do_not_overwrite_existing_outputs(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    configure_workspace(monkeypatch, tmp_path)
    write_source_csv(tmp_path)
    existing = tmp_path / "profile.json"
    existing.write_text("keep-me")

    with pytest.raises(WorkspacePathError, match="already exists"):
        profile_csv("customers.csv", "profile.json")

    assert existing.read_text() == "keep-me"


def test_validate_dataset_rejects_spec_that_does_not_match_manifest(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    configure_workspace(monkeypatch, tmp_path)
    write_source_csv(tmp_path)
    profile_csv("customers.csv", "profile.json")
    infer_dataset_spec(
        output_path="spec.json",
        profile_path="profile.json",
        count=2,
    )
    generate_dataset("spec.json", "generated", output_format="json", seed=7)
    infer_dataset_spec(
        output_path="different_spec.json",
        profile_path="profile.json",
        count=3,
    )

    with pytest.raises(WorkspacePathError, match="does not match"):
        validate_dataset("different_spec.json", "generated")


def test_generate_dataset_rejects_entity_name_path_traversal(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    configure_workspace(monkeypatch, tmp_path)
    write_source_csv(tmp_path)
    profile_csv("customers.csv", "profile.json", table_name="../escaped")
    infer_dataset_spec(output_path="spec.json", profile_path="profile.json", count=2)

    with pytest.raises(ValueError, match="unsafe entity artifact name"):
        generate_dataset("spec.json", "generated", output_format="json", seed=7)

    assert not (tmp_path / "escaped.json").exists()


def test_generate_dataset_rejects_count_above_configured_limit(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    configure_workspace(monkeypatch, tmp_path)
    monkeypatch.setenv("TEST_DATA_AGENT_MAX_GENERATION_COUNT", "3")
    write_source_csv(tmp_path)
    profile_csv("customers.csv", "profile.json")
    infer_dataset_spec(output_path="spec.json", profile_path="profile.json", count=2)

    with pytest.raises(ValueError, match="count must be <= 3"):
        generate_dataset("spec.json", "generated", output_format="json", count=4)


def test_generate_dataset_rejects_spec_row_count_above_configured_limit(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    configure_workspace(monkeypatch, tmp_path)
    monkeypatch.setenv("TEST_DATA_AGENT_MAX_GENERATION_COUNT", "3")
    write_source_csv(tmp_path)
    profile_csv("customers.csv", "profile.json")
    infer_dataset_spec(output_path="spec.json", profile_path="profile.json", count=4)

    with pytest.raises(ValueError, match="entity row_count must be <= 3"):
        generate_dataset("spec.json", "generated", output_format="json")
