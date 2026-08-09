import csv
import json
import shutil
from pathlib import Path

import pytest

import test_data_agent.agent_approval as agent_approval_module
from test_data_agent.core.limits import InputLimitError
from test_data_agent.mcp_generator_server import (
    WorkspacePathError,
    approve_dataset_plan,
    export_dataset,
    generate_dataset,
    infer_dataset_spec,
    inspect_dataset_plan,
    plan_dataset,
    plan_trino_dataset,
    profile_csv,
    recover_dataset_plan,
    resolve_workspace_path,
    validate_dataset,
)
from test_data_agent.safety import ProfileSafetyError, SpecSafetyError


def configure_workspace(monkeypatch: pytest.MonkeyPatch, root: Path) -> None:
    monkeypatch.setenv("TEST_DATA_AGENT_WORKSPACE_ROOT", str(root))


def write_source_csv(root: Path) -> None:
    (root / "customers.csv").write_text(
        "customer_id,email,status\n"
        "1,alice@example.com,active\n"
        "2,bob@example.com,paused\n"
    )


def write_customer_spec(root: Path, *, count: int = 3) -> None:
    write_source_csv(root)
    profile_csv("customers.csv", "profile.json")
    infer_dataset_spec(
        output_path="spec.json",
        profile_path="profile.json",
        count=count,
    )


def test_workspace_paths_reject_escape(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    configure_workspace(monkeypatch, tmp_path)

    with pytest.raises(WorkspacePathError, match="escapes"):
        resolve_workspace_path("../outside.csv")


def test_profile_service_rejects_escape_before_file_io(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    configure_workspace(monkeypatch, tmp_path)

    def unexpected_profile(*args: object, **kwargs: object) -> None:
        raise AssertionError("unsafe path reached CSV profiling")

    monkeypatch.setattr(
        "test_data_agent.mcp_generator_server.write_csv_profile_artifact",
        unexpected_profile,
    )

    with pytest.raises(WorkspacePathError, match="escapes"):
        profile_csv("../outside.csv", "profile.json")


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


def test_infer_dataset_spec_rejects_secret_hidden_in_neutral_category(
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
                        "name": "settings",
                        "row_count": 1,
                        "fields": [
                            {
                                "name": "value",
                                "data_type": "string",
                                "distribution": {
                                    "kind": "categorical",
                                    "categories": [{"value": "sk_live_51ABCDEF", "count": 1}],
                                },
                            }
                        ],
                    }
                ],
            }
        )
    )

    with pytest.raises(ProfileSafetyError, match="raw-looking sensitive values"):
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


def test_plan_and_approve_safe_trino_dataset_through_mcp(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    configure_workspace(monkeypatch, tmp_path)
    profile_payload = {
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
                "name": "status",
                "data_type": "varchar",
                "approx_distinct_count": 2,
                "top_values": [
                    {"value": "paid", "count": 80},
                    {"value": "cancelled", "count": 20},
                ],
            },
            {
                "name": "customer_email",
                "data_type": "varchar",
                "sensitive": True,
                "semantic_type": "email",
                "masked_patterns": [{"pattern": "email", "count": 100}],
            },
            {
                "name": "tax_number",
                "data_type": "bigint",
                "sensitive": True,
                "min_value": 912345678,
                "max_value": 987654321,
                "p05": 923456789,
                "p95": 976543210,
                "numeric_shape": {
                    "max_abs_magnitude": 8,
                    "has_negative": False,
                    "has_positive": True,
                },
            },
        ],
    }

    planned = plan_trino_dataset(
        profile_payload,
        "agent/orders",
        count=4,
        seed=73,
        output_format="json",
    )

    assert planned["operation"] == "plan_trino_dataset"
    assert planned["approval_required"] is True
    assert planned["source_type"] == "trino"
    assert len(planned["plan_id"]) == 32
    assert len(planned["profile_sha256"]) == 64
    assert planned["planned_spec_sha256"] == planned["current_spec_sha256"]
    assert planned["entities"] == [
        {"name": "orders", "row_count": 4, "field_count": 4}
    ]
    assert (tmp_path / "agent" / "orders" / "dataset_spec.yaml").is_file()
    assert not (tmp_path / "agent" / "orders" / "generated").exists()
    assert "paid" not in json.dumps(planned)
    persisted = "\n".join(
        (tmp_path / "agent" / "orders" / name).read_text()
        for name in ("profile.json", "dataset_spec.yaml", "agent_plan.json")
    )
    assert all(
        str(value) not in persisted
        for value in (912345678, 987654321, 923456789, 976543210)
    )
    assert "max_abs_magnitude: 8" in persisted

    inspected = inspect_dataset_plan("agent/orders")
    assert inspected["phase"] == "awaiting_approval"
    assert inspected["next_action"] == "review_and_approve"
    assert (
        inspected["review"]["current_spec_sha256"]
        == planned["current_spec_sha256"]
    )

    approved = approve_dataset_plan(
        "agent/orders",
        inspected["review"]["current_spec_sha256"],
    )
    generated_rows = json.loads(
        (tmp_path / "agent" / "orders" / "generated" / "orders.json").read_text()
    )
    assert all(0 <= row["tax_number"] <= 900_000_000 for row in generated_rows)
    assert any(row["tax_number"] >= 100_000_000 for row in generated_rows)

    assert approved["operation"] == "approve_dataset_plan"
    assert approved["approval_required"] is False
    assert approved["source_type"] == "trino"
    assert approved["row_counts"] == {"orders": 4}
    assert approved["validation_valid"] is True
    assert approved["source_rows_copied"] is False
    assert (
        approved["approval_receipt"]["reviewed_spec_sha256"]
        == planned["current_spec_sha256"]
    )
    assert approved["approval_receipt_path"] == "agent/orders/approval_receipt.json"
    assert len(generated_rows) == 4
    assert "@" in generated_rows[0]["customer_email"]
    assert "customer_email" not in json.dumps(approved)

    completed = inspect_dataset_plan("agent/orders")
    assert completed["phase"] == "completed"
    assert completed["approval_receipt"] == approved["approval_receipt"]


def test_plan_dataset_runs_review_first_csv_flow(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    configure_workspace(monkeypatch, tmp_path)
    write_source_csv(tmp_path)

    planned = plan_dataset(
        "customers.csv",
        "agent/customers",
        count=4,
        seed=81,
        output_format="csv",
        table_name="customers",
    )

    assert planned["operation"] == "plan_dataset"
    assert planned["approval_required"] is True
    assert planned["source_type"] == "csv"
    assert planned["entities"] == [
        {"name": "customers", "row_count": 4, "field_count": 3}
    ]
    assert "alice@example.com" not in json.dumps(planned)
    assert not (tmp_path / "agent" / "customers" / "generated").exists()

    inspected = inspect_dataset_plan("agent/customers")
    approved = approve_dataset_plan(
        "agent/customers",
        inspected["review"]["current_spec_sha256"],
    )
    with (tmp_path / "customers.csv").open(newline="") as handle:
        source_rows = list(csv.DictReader(handle))
    with (
        tmp_path / "agent" / "customers" / "generated" / "customers.csv"
    ).open(newline="") as handle:
        generated_rows = list(csv.DictReader(handle))

    assert approved["row_counts"] == {"customers": 4}
    assert approved["validation_valid"] is True
    assert {tuple(row.items()) for row in source_rows}.isdisjoint(
        {tuple(row.items()) for row in generated_rows}
    )
    assert inspect_dataset_plan("agent/customers")["phase"] == "completed"


def test_plan_dataset_detects_supported_sources_and_rejects_unsafe_inputs(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    configure_workspace(monkeypatch, tmp_path)
    write_source_csv(tmp_path)
    profile_csv("customers.csv", "customers_profile.json")
    inferred = plan_dataset(
        "customers_profile.json",
        "agent/profile",
        count=2,
    )
    request = json.loads((tmp_path / "agent" / "profile" / "agent_request.json").read_text())
    assert inferred["operation"] == "plan_dataset"
    assert request["source_type"] == "profile"

    source_folder = tmp_path / "example"
    shutil.copytree(Path("tests/fixtures/example_dataset"), source_folder)
    folder_plan = plan_dataset("example", "agent/folder", count=2)
    folder_request = json.loads(
        (tmp_path / "agent" / "folder" / "agent_request.json").read_text()
    )
    assert folder_plan["relationship_count"] == 1
    assert folder_request["source_type"] == "csv_folder"

    infer_dataset_spec(
        output_path="dataset_spec.json",
        profile_path="customers_profile.json",
        count=2,
    )
    with pytest.raises(ValueError, match="detected a DatasetSpec"):
        plan_dataset("dataset_spec.json", "agent/spec")
    with pytest.raises(WorkspacePathError, match="escapes"):
        plan_dataset("../outside.csv", "agent/escape")
    with pytest.raises(ValueError, match="source_type must be one of"):
        plan_dataset("customers.csv", "agent/invalid-type", source_type="spreadsheet")  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="must not be inside the source CSV folder"):
        plan_dataset("example", "example/agent")

    assert not (tmp_path / "agent" / "spec").exists()
    assert not (tmp_path / "agent" / "escape").exists()
    assert not (tmp_path / "agent" / "invalid-type").exists()
    assert not (tmp_path / "example" / "agent").exists()


def test_mcp_recovers_interrupted_plan_without_returning_rows(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    configure_workspace(monkeypatch, tmp_path)
    planned = plan_trino_dataset(
        {
            "source_type": "trino",
            "table": "orders",
            "row_count": 10,
            "columns": [
                {
                    "name": "order_id",
                    "data_type": "bigint",
                    "approx_distinct_count": 10,
                }
            ],
        },
        "agent/orders",
        count=3,
    )
    original_publish = agent_approval_module.publish_agent_completion
    monkeypatch.setattr(
        agent_approval_module,
        "publish_agent_completion",
        lambda *args, **kwargs: (_ for _ in ()).throw(RuntimeError("interrupted")),
    )
    with pytest.raises(RuntimeError, match="interrupted"):
        approve_dataset_plan("agent/orders", planned["current_spec_sha256"])
    monkeypatch.setattr(
        agent_approval_module,
        "publish_agent_completion",
        original_publish,
    )

    status = inspect_dataset_plan("agent/orders")
    assert status["phase"] == "recovery_required"
    assert status["next_action"] == "recover"
    assert status["summary"]["reviewed_spec_sha256"] == planned["current_spec_sha256"]

    recovered = recover_dataset_plan(
        "agent/orders",
        planned["current_spec_sha256"],
    )
    assert recovered["operation"] == "recover_dataset_plan"
    assert recovered["row_counts"] == {"orders": 3}
    assert "rows" not in recovered
    assert inspect_dataset_plan("agent/orders")["phase"] == "completed"


def test_plan_trino_dataset_rejects_non_trino_and_oversized_profiles(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    configure_workspace(monkeypatch, tmp_path)

    with pytest.raises(ValueError, match="only a profile returned by Trino MCP"):
        plan_trino_dataset(
            {
                "source_type": "manual",
                "entities": [],
            },
            "agent/non-trino",
        )

    monkeypatch.setenv("TEST_DATA_AGENT_MAX_PROFILE_PAYLOAD_BYTES", "128")
    with pytest.raises(InputLimitError, match="profile payload must be <= 128"):
        plan_trino_dataset(
            {
                "source_type": "trino",
                "table": "orders",
                "row_count": 1,
                "columns": [
                    {
                        "name": "status",
                        "data_type": "varchar",
                        "top_values": [{"value": "x" * 256, "count": 1}],
                    }
                ],
            },
            "agent/oversized",
        )

    assert not (tmp_path / "agent").exists()


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


def test_generate_dataset_rejects_raw_sensitive_category_before_output(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    configure_workspace(monkeypatch, tmp_path)
    raw_email = "private-person@example.com"
    (tmp_path / "unsafe_spec.json").write_text(
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

    with pytest.raises(SpecSafetyError) as error:
        generate_dataset("unsafe_spec.json", "generated", seed=7)

    assert raw_email not in str(error.value)
    assert not (tmp_path / "generated").exists()


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


def test_generate_dataset_applies_inline_business_rules_and_records_manifest(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    configure_workspace(monkeypatch, tmp_path)
    write_customer_spec(tmp_path)

    result = generate_dataset(
        "spec.json",
        "generated",
        output_format="json",
        seed=17,
        business_rules_payload={
            "field_rules": [
                {
                    "table": "customers",
                    "field": "status",
                    "allowed_values": ["reviewed"],
                }
            ]
        },
    )

    rows = json.loads((tmp_path / "generated" / "customers.json").read_text())
    manifest = json.loads(
        (tmp_path / "generated" / "generation_manifest.json").read_text()
    )
    report = json.loads(
        (tmp_path / "generated" / "business_validation_report.json").read_text()
    )
    validated = validate_dataset("generated/dataset_spec.yaml", "generated")

    assert {row["status"] for row in rows} == {"reviewed"}
    assert result["business_validation"]["valid"] is True
    assert result["business_validation"]["rule_count"] == 1
    assert len(result["business_validation"]["rules_sha256"]) == 64
    assert result["business_validation_report_path"] == (
        "generated/business_validation_report.json"
    )
    assert "reviewed" not in json.dumps(result)
    assert manifest["business_validation"] == result["business_validation"]
    assert report["rules_sha256"] == manifest["business_validation"]["rules_sha256"]
    assert validated["business_validation"] == result["business_validation"]
    assert validated["business_validation_report_path"] == (
        "generated/business_validation_report.json"
    )


def test_export_dataset_accepts_workspace_business_rule_file(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    configure_workspace(monkeypatch, tmp_path)
    write_customer_spec(tmp_path, count=2)
    (tmp_path / "rules.yaml").write_text(
        """
field_rules:
  - table: customers
    field: status
    required: true
"""
    )

    result = export_dataset(
        "spec.json",
        "exported",
        output_format="json",
        seed=23,
        business_rules_path="rules.yaml",
    )

    assert result["business_validation"]["valid"] is True
    assert result["manifest_path"] == "exported/generation_manifest.json"


def test_generate_dataset_rejects_ambiguous_or_unsafe_business_rules(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    configure_workspace(monkeypatch, tmp_path)
    write_customer_spec(tmp_path)
    (tmp_path / "rules.yaml").write_text("field_rules: []\n")

    with pytest.raises(ValueError, match="provide at most one"):
        generate_dataset(
            "spec.json",
            "ambiguous",
            business_rules_path="rules.yaml",
            business_rules_payload={"field_rules": []},
        )

    with pytest.raises(ValueError, match="unknown field"):
        generate_dataset(
            "spec.json",
            "unknown",
            business_rules_payload={
                "field_rules": [
                    {
                        "table": "customers",
                        "field": "missing",
                        "required": True,
                    }
                ]
            },
        )

    with pytest.raises(ValueError, match="raw-looking sensitive value"):
        generate_dataset(
            "spec.json",
            "raw-pii",
            business_rules_payload={
                "field_rules": [
                    {
                        "table": "customers",
                        "field": "status",
                        "allowed_values": ["victim@example.com"],
                    }
                ]
            },
        )

    with pytest.raises(ValueError, match="sensitive field values"):
        generate_dataset(
            "spec.json",
            "sensitive-target",
            business_rules_payload={
                "scenarios": [
                    {
                        "name": "fixed-email",
                        "weight": 1,
                        "field_values": {
                            "customers": {"email": "synthetic@example.test"}
                        },
                    }
                ]
            },
        )

    assert not any(
        (tmp_path / name).exists()
        for name in ("ambiguous", "unknown", "raw-pii", "sensitive-target")
    )


def test_generate_dataset_rejects_unknown_keys_and_oversized_rule_payload(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    configure_workspace(monkeypatch, tmp_path)
    write_customer_spec(tmp_path)

    with pytest.raises(ValueError, match="extra_forbidden"):
        generate_dataset(
            "spec.json",
            "unknown-key",
            business_rules_payload={
                "field_rules": [
                    {
                        "table": "customers",
                        "field": "status",
                        "required": True,
                        "typo": True,
                    }
                ]
            },
        )

    monkeypatch.setenv("TEST_DATA_AGENT_MAX_BUSINESS_RULES_BYTES", "128")
    with pytest.raises(InputLimitError, match="payload must be <= 128 bytes"):
        generate_dataset(
            "spec.json",
            "oversized",
            business_rules_payload={
                "field_rules": [
                    {
                        "table": "customers",
                        "field": "status",
                        "allowed_values": ["x" * 256],
                    }
                ]
            },
        )

    assert not (tmp_path / "unknown-key").exists()
    assert not (tmp_path / "oversized").exists()


def test_generate_dataset_rejects_excessive_business_rule_work(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    configure_workspace(monkeypatch, tmp_path)
    write_customer_spec(tmp_path, count=3)
    monkeypatch.setenv("TEST_DATA_AGENT_MAX_BUSINESS_RULE_EVALUATIONS", "2")

    with pytest.raises(InputLimitError, match="more than 2 estimated evaluations"):
        generate_dataset(
            "spec.json",
            "excessive-work",
            business_rules_payload={
                "field_rules": [
                    {
                        "table": "customers",
                        "field": "status",
                        "required": True,
                    }
                ]
            },
        )

    assert not (tmp_path / "excessive-work").exists()


def test_generate_dataset_rejects_excessively_nested_business_rules(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    configure_workspace(monkeypatch, tmp_path)
    write_customer_spec(tmp_path)

    def fail_serialization(*args: object, **kwargs: object) -> str:
        raise RecursionError

    monkeypatch.setattr(
        "test_data_agent.mcp_generator_server.json.dumps",
        fail_serialization,
    )

    with pytest.raises(ValueError, match="JSON-compatible"):
        generate_dataset(
            "spec.json",
            "deep-rules",
            business_rules_payload={"field_rules": []},
        )

    assert not (tmp_path / "deep-rules").exists()


def test_validate_dataset_rejects_tampered_business_validation_report(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    configure_workspace(monkeypatch, tmp_path)
    write_customer_spec(tmp_path)
    generate_dataset(
        "spec.json",
        "generated",
        output_format="json",
        seed=29,
        business_rules_payload={
            "field_rules": [
                {
                    "table": "customers",
                    "field": "status",
                    "required": True,
                }
            ]
        },
    )
    report_path = tmp_path / "generated" / "business_validation_report.json"
    report = json.loads(report_path.read_text())
    report["rule_pass_count"] += 1
    report_path.write_text(json.dumps(report))

    with pytest.raises(WorkspacePathError, match="does not match"):
        validate_dataset("generated/dataset_spec.yaml", "generated")
