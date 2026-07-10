import csv
import json
from pathlib import Path

from test_data_agent.cli import main
from test_data_agent.core.constraint import ConstraintType
from test_data_agent.core.dataset import DatasetSpec
from test_data_agent.core.entity import EntitySpec
from test_data_agent.core.field import FieldSpec, FieldType
from test_data_agent.generation import generate_dataset, infer_dataset_spec
from test_data_agent.profiling import profile_example_folder
from test_data_agent.profiling.cache import csv_folder_fingerprint
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
