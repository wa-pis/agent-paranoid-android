import csv
import json
from pathlib import Path

import pytest

from test_data_agent.cli import main
from test_data_agent.core.constraint import ConstraintType
from test_data_agent.core.dataset import DatasetProfile, DatasetSpec
from test_data_agent.core.entity import EntitySpec
from test_data_agent.core.field import FieldSpec, FieldType
from test_data_agent.core.privacy import LocalCategoryField
from test_data_agent.generation import generate_dataset, infer_dataset_spec
from test_data_agent.profiling import load_csv_folder, profile_example_folder
from test_data_agent.profiling.cache import (
    PROFILE_CACHE_FORMAT_VERSION,
    csv_folder_fingerprint,
    load_cached_profile,
)
from test_data_agent.profiling.schema_profiler import _sanitize_source_categories
from test_data_agent.validation import validate_dataset


FIXTURE = Path(__file__).parent / "fixtures" / "example_dataset"


def test_schema_profiling_masks_pii_and_finds_fields() -> None:
    profile = profile_example_folder(FIXTURE)
    profile_json = profile.model_dump_json()
    customers = profile.entity("customers")
    email = customers.field("email")

    assert {entity.name for entity in profile.entities} == {"customers", "orders"}
    assert email.sensitive is True
    assert "alice@example.com" not in profile_json
    assert "C1" not in profile_json
    assert customers.primary_key_candidates == ["customer_id"]


def test_folder_csv_profiling_detects_semicolon_delimiter_and_bom(tmp_path) -> None:
    source = tmp_path / "customers.csv"
    source.write_bytes(
        "\ufeffcustomer_id;email;status\n"
        "1;alice@example.com;active\n"
        "2;bob@example.com;paused\n".encode("utf-8")
    )

    profile = profile_example_folder(tmp_path, cache_dir=None)
    rows_by_entity = load_csv_folder(tmp_path)
    customers = profile.entity("customers")

    assert [field.name for field in customers.fields] == ["customer_id", "email", "status"]
    assert customers.field("email").sensitive is True
    assert "alice@example.com" not in profile.model_dump_json()
    assert rows_by_entity["customers"][0] == {
        "customer_id": "1",
        "email": "alice@example.com",
        "status": "active",
    }


def test_folder_profile_streams_schema_and_rule_sample_in_one_text_pass(
    tmp_path,
    monkeypatch,
) -> None:
    source = tmp_path / "customers.csv"
    source.write_text("customer_id,status\n1,active\n2,paused\n")
    original_open = Path.open
    text_opens = 0

    def counting_open(path, mode="r", *args, **kwargs):
        nonlocal text_opens
        if path == source and "b" not in mode:
            text_opens += 1
        return original_open(path, mode, *args, **kwargs)

    monkeypatch.setattr(Path, "open", counting_open)

    profile = profile_example_folder(
        tmp_path,
        cache_dir=None,
        rule_sample_rows=1,
    )

    assert profile.entity("customers").row_count == 2
    assert text_opens == 1


def test_folder_profile_replaces_source_categories_without_losing_conditions(
    tmp_path,
) -> None:
    source = tmp_path / "source"
    source.mkdir()
    (source / "events.csv").write_text(
        "event_id,segment,detail,metric\n"
        "1,opaque_alpha,filled,9.12345678e8\n"
        "2,opaque_alpha,filled,9.12345679e8\n"
        "3,opaque_alpha,filled,9.12345680e8\n"
        "4,opaque_beta,,9.12345681e8\n"
        "5,category_1,,9.12345682e8\n"
    )
    cache_dir = tmp_path / "cache"
    cache_file = cache_dir / f"{csv_folder_fingerprint(source)}.json"

    profile = profile_example_folder(source, cache_dir=cache_dir)
    spec = infer_dataset_spec(profile, count=32)
    rows_a = generate_dataset(spec, seed=123)
    rows_b = generate_dataset(spec, seed=123)
    serialized = (
        profile.model_dump_json()
        + spec.model_dump_json()
        + cache_file.read_text()
        + json.dumps(rows_a)
    )
    conditional = next(
        constraint
        for constraint in profile.constraints
        if constraint.type == ConstraintType.CONDITIONAL_REQUIRED
    )

    assert "opaque_alpha" not in serialized
    assert "opaque_beta" not in serialized
    assert "filled" not in serialized
    assert profile.entity("events").field("segment").distribution == {
        "kind": "categorical",
        "categories": [
            {"value": "category_1_1", "count": 3},
            {"value": "category_2", "count": 1},
            {"value": "category_3", "count": 1},
        ],
    }
    assert conditional.condition == {"field": "segment", "equals": "category_1_1"}
    assert profile.entity("events").field("metric").distribution == {
        "kind": "numeric",
        "min_value": 912345678.0,
        "max_value": 912345682.0,
        "p05": 912345678.2,
        "p95": 912345681.8,
        "scale_factor": 1.0,
    }
    assert rows_a == rows_b
    assert {row["segment"] for row in rows_a["events"]}.isdisjoint(
        {"opaque_alpha", "opaque_beta", "category_1"}
    )
    assert any(row["segment"] == "category_1_1" for row in rows_a["events"])
    assert all(
        row["detail"] is not None
        for row in rows_a["events"]
        if row["segment"] == "category_1_1"
    )
    assert validate_dataset(rows_a, spec).valid is True


def test_folder_profile_preserves_allowlisted_local_categories(tmp_path) -> None:
    source = tmp_path / "source"
    source.mkdir()
    (source / "events.csv").write_text(
        "event_id,segment,detail\n"
        "1,active,filled\n"
        "2,active,filled\n"
        "3,paused,filled\n"
        "4,failed,\n"
    )

    allowed_field = LocalCategoryField(entity="events", field="segment")
    profile = profile_example_folder(
        source,
        cache_dir=None,
        local_category_fields=(allowed_field,),
    )
    segment_distribution = profile.entity("events").field("segment").distribution

    assert profile.local_category_fields == [allowed_field]
    assert segment_distribution == {
        "kind": "categorical",
        "categories": [
            {"value": "active", "count": 2},
            {"value": "paused", "count": 1},
            {"value": "failed", "count": 1},
        ],
    }

    conditional = next(
        constraint
        for constraint in profile.constraints
        if constraint.type == ConstraintType.CONDITIONAL_REQUIRED
    )
    assert conditional.condition == {"field": "segment", "equals": "active"}


def test_folder_profile_rejects_unsafe_local_category_allowlist(tmp_path) -> None:
    source = tmp_path / "source"
    source.mkdir()
    (source / "events.csv").write_text(
        "event_id,segment\n"
        "1,customer note with too much personal context\n"
        "2,another private narrative with identifiers 12345\n"
    )

    allowed_field = LocalCategoryField(entity="events", field="segment")

    with pytest.raises(ValueError, match="not safe for raw preservation"):
        profile_example_folder(
            source,
            cache_dir=None,
            local_category_fields=(allowed_field,),
        )


def test_folder_profile_rejects_too_many_local_categories_for_allowlist() -> None:
    profile = DatasetProfile.model_validate(
        {
            "entities": [
                {
                    "name": "events",
                    "row_count": 21,
                    "fields": [
                        {
                            "name": "segment",
                            "data_type": "string",
                            "distribution": {
                                "kind": "categorical",
                                "categories": [
                                    {"value": f"category_{idx}", "count": 1}
                                    for idx in range(25)
                                ],
                            },
                        }
                    ],
                }
            ]
        }
    )

    with pytest.raises(ValueError, match="not safe for raw preservation"):
        _sanitize_source_categories(
            profile,
            local_category_fields=(LocalCategoryField(entity="events", field="segment"),),
        )


def test_relationship_inference() -> None:
    profile = profile_example_folder(FIXTURE)

    assert any(
        relationship.parent_entity == "customers"
        and relationship.parent_field == "customer_id"
        and relationship.child_entity == "orders"
        and relationship.child_field == "customer_id"
        and relationship.confidence == 1.0
        for relationship in profile.relationships
    )


def test_formula_temporal_conditional_and_aggregate_inference() -> None:
    profile = profile_example_folder(FIXTURE)
    constraint_types = {constraint.type for constraint in profile.constraints}

    assert ConstraintType.FORMULA in constraint_types
    assert ConstraintType.TEMPORAL in constraint_types
    assert ConstraintType.CONDITIONAL_REQUIRED in constraint_types
    assert ConstraintType.AGGREGATE_MAPPING in constraint_types
    assert all(constraint.confidence > 0 for constraint in profile.constraints)
    assert all(constraint.status == "inferred" for constraint in profile.constraints)


def test_deterministic_generation_no_copied_rows_and_validation_passes() -> None:
    profile = profile_example_folder(FIXTURE)
    spec = infer_dataset_spec(profile, count=10)
    rows_a = generate_dataset(spec, seed=123)
    rows_b = generate_dataset(spec, seed=123)
    report = validate_dataset(rows_a, spec)
    source_rows = load_source_rows(FIXTURE)

    assert rows_a == rows_b
    assert report.valid is True
    assert not copied_rows(rows_a, source_rows)
    assert {row["customer_id"] for row in rows_a["orders"]} <= {row["customer_id"] for row in rows_a["customers"]}


def test_dataset_validation_rejects_wrong_entity_row_count() -> None:
    spec = DatasetSpec(
        entities=[
            EntitySpec(
                name="events",
                row_count=2,
                fields=[FieldSpec(name="event_id", data_type=FieldType.INTEGER, is_identifier=True)],
            )
        ]
    )

    report = validate_dataset({"events": [{"event_id": 1}]}, spec)

    assert report.valid is False
    assert report.sections[0].errors == ["events row count mismatch: expected 2, got 1"]


def test_validation_settings_control_sections_and_fail_fast() -> None:
    spec = DatasetSpec(
        entities=[
            EntitySpec(
                name="events",
                row_count=1,
                fields=[FieldSpec(name="event_id", data_type=FieldType.INTEGER)],
            )
        ],
        validation_settings={
            "validate_relationships": False,
            "validate_constraints": False,
            "validate_privacy": False,
            "fail_fast": True,
        },
    )

    report = validate_dataset({"events": [{"event_id": "wrong"}]}, spec)

    assert report.valid is False
    assert [item.name for item in report.sections] == ["schema"]
    assert report.settings == spec.validation_settings


def test_validation_can_disable_schema_section() -> None:
    spec = DatasetSpec(
        entities=[
            EntitySpec(
                name="events",
                row_count=1,
                fields=[FieldSpec(name="event_id", data_type=FieldType.INTEGER)],
            )
        ],
        validation_settings={"validate_schema": False},
    )

    report = validate_dataset({"events": [{"event_id": "wrong"}]}, spec)

    assert report.valid is True
    assert [item.name for item in report.sections] == [
        "relationships",
        "constraints",
        "privacy",
    ]


def test_privacy_validation_reports_unsafe_spec_policy() -> None:
    spec = DatasetSpec(entities=[])
    spec.privacy_settings.allow_raw_sensitive_values = True

    report = validate_dataset({}, spec)

    assert report.valid is False
    assert report.sections[-1].name == "privacy"
    assert report.sections[-1].errors == [
        "dataset spec cannot allow raw sensitive values"
    ]


def test_generation_uses_typed_distribution_models() -> None:
    spec = DatasetSpec(
        entities=[
            EntitySpec(
                name="events",
                row_count=20,
                fields=[
                    FieldSpec(
                        name="status",
                        data_type=FieldType.STRING,
                        distribution={
                            "kind": "categorical",
                            "categories": [
                                {"value": "new", "count": 3},
                                {"value": "done", "count": 1},
                            ],
                        },
                    ),
                    FieldSpec(
                        name="amount",
                        data_type=FieldType.FLOAT,
                        distribution={"kind": "numeric", "p05": 10, "p95": 20},
                    ),
                    FieldSpec(
                        name="is_active",
                        data_type=FieldType.BOOLEAN,
                        distribution={"kind": "boolean", "true_ratio": 1.0},
                    ),
                    FieldSpec(
                        name="event_date",
                        data_type=FieldType.DATE,
                        distribution={"kind": "date_range", "min": "2024-01-01", "max": "2024-01-03"},
                    ),
                    FieldSpec(
                        name="code",
                        data_type=FieldType.STRING,
                        distribution={"kind": "string_pattern", "min_length": 4, "max_length": 4},
                    ),
                ],
            )
        ]
    )

    rows = generate_dataset(spec, seed=17)["events"]

    assert {row["status"] for row in rows} <= {"new", "done"}
    assert all(10 <= row["amount"] <= 20 for row in rows)
    assert all(row["is_active"] is True for row in rows)
    assert all("2024-01-01" <= row["event_date"] <= "2024-01-03" for row in rows)
    assert all(len(row["code"]) == 8 for row in rows)


def test_cli_profile_infer_generate_validate_and_generate_from_example(tmp_path) -> None:
    profile_path = tmp_path / "profile.json"
    spec_path = tmp_path / "dataset_spec.yaml"
    generated = tmp_path / "generated"
    generated_direct = tmp_path / "generated_direct"
    validation_report = tmp_path / "validation_report.json"

    assert main(["profile-example", str(FIXTURE), "--output", str(profile_path)]) == 0
    assert main(["infer-spec", str(profile_path), "--output", str(spec_path), "--count", "8"]) == 0
    assert main(["generate", str(spec_path), "--seed", "777", "--format", "csv", "--output", str(generated)]) == 0
    assert main(["validate", str(spec_path), str(generated), "--output", str(validation_report)]) == 0
    assert main(
        [
            "generate-from-example",
            str(FIXTURE),
            "--seed",
            "777",
            "--count",
            "8",
            "--format",
            "json",
            "--output",
            str(generated_direct),
        ]
    ) == 0

    assert (generated / "customers.csv").exists()
    assert (generated / "orders.csv").exists()
    assert json.loads(validation_report.read_text())["valid"] is True
    assert (generated_direct / "profile.json").exists()
    assert (generated_direct / "dataset_spec.yaml").exists()
    assert (generated_direct / "validation_report.json").exists()


def test_generate_from_example_writes_review_artifacts(tmp_path) -> None:
    output_dir = tmp_path / "generated_direct"

    exit_code = main(
        [
            "generate-from-example",
            str(FIXTURE),
            "--seed",
            "101",
            "--count",
            "4",
            "--format",
            "json",
            "--output",
            str(output_dir),
        ]
    )

    profile = json.loads((output_dir / "profile.json").read_text())
    spec_yaml = (output_dir / "dataset_spec.yaml").read_text()
    report = json.loads((output_dir / "validation_report.json").read_text())

    assert exit_code == 0
    assert profile["source_type"] == "csv_folder"
    assert "entities:" in spec_yaml
    assert "customers" in spec_yaml
    assert report["valid"] is True


def test_profile_example_uses_safe_profile_cache(tmp_path) -> None:
    cache_dir = tmp_path / "cache"

    profile_a = profile_example_folder(FIXTURE, cache_dir=cache_dir)
    cache_file = cache_dir / f"{csv_folder_fingerprint(FIXTURE)}.json"
    profile_b = profile_example_folder(FIXTURE, cache_dir=cache_dir)

    assert cache_file.exists()
    assert "alice@example.com" not in cache_file.read_text()
    assert profile_a == profile_b


def test_profile_cache_treats_fingerprint_mismatch_as_cache_miss(tmp_path) -> None:
    source = tmp_path / "source"
    source.mkdir()
    (source / "customers.csv").write_text("customer_id,status\n1,active\n")
    cache_dir = tmp_path / "cache"
    cache_dir.mkdir()
    cache_file = cache_dir / f"{csv_folder_fingerprint(source)}.json"
    cache_file.write_text(
        json.dumps(
            {
                "format_version": PROFILE_CACHE_FORMAT_VERSION,
                "fingerprint": "wrong",
                "profile": {
                    "source_type": "csv_folder",
                    "entities": [],
                },
            }
        )
    )

    assert load_cached_profile(source, cache_dir=cache_dir) is None


def test_profile_cache_treats_legacy_format_as_cache_miss(tmp_path) -> None:
    source = tmp_path / "source"
    source.mkdir()
    (source / "customers.csv").write_text("customer_id,status\n1,opaque_source\n")
    cache_dir = tmp_path / "cache"
    cache_dir.mkdir()
    cache_file = cache_dir / f"{csv_folder_fingerprint(source)}.json"
    cache_file.write_text(
        json.dumps(
            {
                "fingerprint": csv_folder_fingerprint(source),
                "profile": {"source_type": "csv_folder", "entities": []},
            }
        )
    )

    profile = profile_example_folder(source, cache_dir=cache_dir)
    cached_payload = json.loads(cache_file.read_text())

    assert profile.entity("customers").row_count == 1
    assert "opaque_source" not in cache_file.read_text()
    assert cached_payload["format_version"] == PROFILE_CACHE_FORMAT_VERSION


def test_profile_cache_key_includes_rule_sample_size(tmp_path) -> None:
    source = tmp_path / "source"
    source.mkdir()
    (source / "customers.csv").write_text("customer_id,status\n1,active\n2,paused\n")
    cache_dir = tmp_path / "cache"

    profile_example_folder(source, cache_dir=cache_dir, rule_sample_rows=1)
    profile_example_folder(source, cache_dir=cache_dir, rule_sample_rows=2)

    assert len(list(cache_dir.glob("*.json"))) == 2


def load_source_rows(folder: Path) -> dict[str, list[dict[str, str]]]:
    rows = {}
    for path in folder.glob("*.csv"):
        with path.open(newline="") as handle:
            rows[path.stem] = [dict(row) for row in csv.DictReader(handle)]
    return rows


def copied_rows(generated: dict[str, list[dict]], source: dict[str, list[dict[str, str]]]) -> bool:
    for table, rows in generated.items():
        generated_normalized = {tuple((key, str(value)) for key, value in row.items()) for row in rows}
        source_normalized = {tuple(row.items()) for row in source.get(table, [])}
        if generated_normalized & source_normalized:
            return True
    return False
