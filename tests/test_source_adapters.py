import json
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq
import pytest
import test_data_agent.adapters as adapters_package

from test_data_agent.adapters import (
    dataset_profile_from_csv_file,
    dataset_profile_from_csv_folder,
    dataset_profile_from_parquet,
    dataset_spec_from_csv_folder,
    dataset_spec_from_trino_profile,
    load_profile_or_spec,
)
from test_data_agent.adapters.legacy_generation import (
    dataset_spec_from_generation_spec,
    dataset_spec_to_generation_spec,
    generate_legacy_compatibility_result,
    generate_legacy_rows,
    legacy_profile_to_generation_spec,
    load_legacy_generation_spec,
    prepare_legacy_generation_spec,
    validate_legacy_rows_file,
    validate_legacy_rows_report,
)
from test_data_agent.core.dataset import DatasetProfile, DatasetSpec
from test_data_agent.core.entity import EntitySpec
from test_data_agent.core.field import FieldSpec, FieldType
from test_data_agent.spec import ColumnSpec, DataType, GenerationSpec, TableSpec


FIXTURE_CSV = Path(__file__).parent / "fixtures" / "customers.csv"
FIXTURE_FOLDER = Path(__file__).parent / "fixtures" / "example_dataset"


def test_csv_file_adapter_builds_safe_one_entity_profile() -> None:
    profile = dataset_profile_from_csv_file(FIXTURE_CSV)
    profile_json = profile.model_dump_json()
    customers = profile.entity("customers")
    email = customers.field("email")

    assert profile.source_type == "csv"
    assert customers.row_count == 5
    assert email.sensitive is True
    assert email.distribution["kind"] == "masked_patterns"
    assert "alice@example.com" not in profile_json


def test_csv_folder_adapter_builds_safe_multi_entity_profile() -> None:
    profile = dataset_profile_from_csv_folder(FIXTURE_FOLDER, use_cache=False)
    customers = profile.entity("customers")

    assert profile.source_type == "csv_folder"
    assert {entity.name for entity in profile.entities} == {"customers", "orders"}
    assert customers.field("email").sensitive is True
    assert any(
        relationship.parent_entity == "customers"
        and relationship.child_entity == "orders"
        for relationship in profile.relationships
    )
    assert "alice@example.com" not in profile.model_dump_json()


def test_csv_folder_adapter_builds_dataset_spec_with_seed_and_relationships() -> None:
    spec = dataset_spec_from_csv_folder(FIXTURE_FOLDER, count=7, seed=123, use_cache=False)

    assert spec.generation_settings.seed == 123
    assert spec.entity("customers").row_count == 7
    assert spec.entity("orders").row_count == 7
    assert any(
        relationship.parent_entity == "customers"
        and relationship.child_entity == "orders"
        for relationship in spec.relationships
    )


def test_trino_profile_adapter_uses_safe_metadata_only() -> None:
    spec = dataset_spec_from_trino_profile(
        {
            "source_type": "trino",
            "table": "orders",
            "row_count": 100,
            "columns": [
                {"name": "order_id", "data_type": "bigint", "approx_distinct_count": 100, "non_null_count": 100},
                {
                    "name": "status",
                    "data_type": "varchar",
                    "top_values": [{"value": "paid", "count": 80}, {"value": "cancelled", "count": 20}],
                    "approx_distinct_count": 2,
                    "non_null_count": 100,
                },
                {
                    "name": "customer_email",
                    "data_type": "varchar",
                    "top_values": [{"value": "alice@example.com", "count": 1}],
                    "approx_distinct_count": 100,
                    "non_null_count": 100,
                },
            ],
        },
        count=10,
    )

    orders = spec.entity("orders")
    email = orders.field("customer_email")
    status = orders.field("status")

    assert orders.row_count == 10
    assert orders.primary_key == "order_id"
    assert status.distribution["kind"] == "categorical"
    assert email.sensitive is True
    assert "alice@example.com" not in spec.model_dump_json()


def test_legacy_generation_spec_adapter_preserves_generation_settings() -> None:
    legacy_spec = GenerationSpec(
        seed=42,
        table=TableSpec(
            name="customers",
            row_count=3,
            columns=[
                ColumnSpec(name="id", data_type=DataType.INTEGER, strategy="sequence"),
                ColumnSpec(name="email", data_type=DataType.EMAIL),
            ],
        ),
    )

    spec = dataset_spec_from_generation_spec(legacy_spec)

    assert spec.generation_settings.seed == 42
    assert spec.entity("customers").primary_key == "id"
    assert spec.entity("customers").field("email").sensitive is True


def test_adapters_package_root_excludes_redundant_generation_spec_alias() -> None:
    assert not hasattr(adapters_package, "dataset_spec_from_generation_spec")


def test_legacy_generation_adapter_can_generate_rows() -> None:
    legacy_spec = GenerationSpec(
        seed=42,
        table=TableSpec(
            name="customers",
            row_count=2,
            columns=[
                ColumnSpec(name="id", data_type=DataType.INTEGER, strategy="sequence"),
                ColumnSpec(name="email", data_type=DataType.EMAIL),
            ],
        ),
    )

    with pytest.deprecated_call(match="GenerationSpec compatibility is deprecated"):
        rows = generate_legacy_rows(legacy_spec)

    assert len(rows) == 2
    assert rows[0]["id"] == 1
    assert rows[0]["email"] != rows[1]["email"]


def test_legacy_generation_adapter_loads_specs_from_disk(tmp_path) -> None:
    path = tmp_path / "legacy_spec.json"
    legacy_spec = GenerationSpec(
        seed=42,
        table=TableSpec(
            name="customers",
            row_count=2,
            columns=[
                ColumnSpec(name="id", data_type=DataType.INTEGER, strategy="sequence"),
                ColumnSpec(name="email", data_type=DataType.EMAIL),
            ],
        ),
    )
    path.write_text(legacy_spec.model_dump_json())

    with pytest.deprecated_call(match="GenerationSpec compatibility is deprecated"):
        loaded = load_legacy_generation_spec(path)

    assert loaded == legacy_spec


def test_legacy_generation_adapter_prepares_cli_overrides(tmp_path) -> None:
    path = tmp_path / "legacy_spec.json"
    legacy_spec = GenerationSpec(
        seed=42,
        table=TableSpec(
            name="customers",
            row_count=2,
            columns=[
                ColumnSpec(name="id", data_type=DataType.INTEGER, strategy="sequence"),
                ColumnSpec(name="email", data_type=DataType.EMAIL),
            ],
        ),
    )
    path.write_text(legacy_spec.model_dump_json())

    with pytest.deprecated_call(match="GenerationSpec compatibility is deprecated"):
        prepared = prepare_legacy_generation_spec(
            path,
            row_count=5,
            seed=7,
            mode="mixed",
            invalid_ratio=0.25,
        )

    assert prepared.seed == 7
    assert prepared.table.row_count == 5
    assert [column.invalid_ratio for column in prepared.table.columns] == [0.25, 0.25]


def test_legacy_generation_adapter_runs_compatibility_workflow(tmp_path) -> None:
    path = tmp_path / "legacy_spec.json"
    legacy_spec = GenerationSpec(
        seed=42,
        table=TableSpec(
            name="customers",
            row_count=2,
            columns=[
                ColumnSpec(name="id", data_type=DataType.INTEGER, strategy="sequence"),
                ColumnSpec(name="email", data_type=DataType.EMAIL),
            ],
        ),
    )
    path.write_text(legacy_spec.model_dump_json())

    with pytest.deprecated_call(match="GenerationSpec compatibility is deprecated"):
        result = generate_legacy_compatibility_result(path, seed=7, row_count=3)

    assert result.spec.seed == 7
    assert result.spec.table.row_count == 3
    assert result.dataset_spec.generation_settings.seed == 7
    assert len(result.rows) == 3
    assert result.rows[0]["id"] == 7000001
    assert result.report.valid is True


def test_legacy_generation_adapter_validates_rows_through_compatibility_boundary() -> None:
    legacy_spec = GenerationSpec(
        seed=42,
        table=TableSpec(
            name="customers",
            row_count=2,
            columns=[
                ColumnSpec(name="id", data_type=DataType.INTEGER, strategy="sequence"),
                ColumnSpec(name="email", data_type=DataType.EMAIL),
            ],
        ),
    )

    with pytest.deprecated_call(match="GenerationSpec compatibility is deprecated"):
        report = validate_legacy_rows_report(
            [{"id": 1, "email": "synthetic@example.test"}],
            legacy_spec,
        )

    assert report.valid is False
    assert report.error_count == 1
    assert report.errors == ["expected 2 rows, got 1"]


def test_legacy_generation_adapter_validates_row_files(tmp_path) -> None:
    spec_path = tmp_path / "legacy_spec.json"
    rows_path = tmp_path / "rows.json"
    legacy_spec = GenerationSpec(
        seed=42,
        table=TableSpec(
            name="customers",
            row_count=2,
            columns=[
                ColumnSpec(name="id", data_type=DataType.INTEGER, strategy="sequence"),
                ColumnSpec(name="email", data_type=DataType.EMAIL),
            ],
        ),
    )
    spec_path.write_text(legacy_spec.model_dump_json())
    rows_path.write_text(json.dumps([{"id": 1, "email": "synthetic@example.test"}]))

    with pytest.deprecated_call(match="GenerationSpec compatibility is deprecated"):
        report = validate_legacy_rows_file(spec_path, rows_path)

    assert report.valid is False
    assert report.errors == ["expected 2 rows, got 1"]


def test_legacy_profile_adapter_can_build_generation_spec_via_dataset_spec() -> None:
    with pytest.deprecated_call(match="GenerationSpec compatibility is deprecated"):
        spec = legacy_profile_to_generation_spec(
            {
                "table": "orders",
                "columns": [
                    {"name": "order_id", "data_type": "bigint", "approx_distinct_count": 100},
                    {
                        "name": "status",
                        "data_type": "varchar",
                        "top_values": [{"value": "new", "count": 60}, {"value": "shipped", "count": 40}],
                        "approx_distinct_count": 2,
                    },
                ],
            },
            count=12,
            seed=9,
        )

    assert spec.seed == 9
    assert spec.table.name == "orders"
    assert spec.table.row_count == 12
    assert spec.table.columns[0].strategy == "sequence"
    assert spec.table.columns[1].choices == ["new", "shipped"]


def test_dataset_spec_to_generation_spec_uses_typed_distribution_metadata() -> None:
    spec = DatasetSpec(
        generation_settings={"seed": 11},
        entities=[
            EntitySpec(
                name="orders",
                row_count=4,
                fields=[
                    FieldSpec(
                        name="status",
                        data_type=FieldType.STRING,
                        distribution={
                            "kind": "categorical",
                            "categories": [
                                {"value": "new", "count": 3},
                                {"value": "shipped", "count": 1},
                            ],
                        },
                    ),
                    FieldSpec(
                        name="amount",
                        data_type=FieldType.FLOAT,
                        distribution={"kind": "numeric", "p05": 10, "p95": 99},
                    ),
                    FieldSpec(
                        name="created_at",
                        data_type=FieldType.DATETIME,
                        distribution={
                            "kind": "datetime_range",
                            "min": "2024-01-01T00:00:00",
                            "max": "2024-12-31T23:59:59",
                        },
                    ),
                ],
            )
        ],
    )

    with pytest.deprecated_call(match="GenerationSpec compatibility is deprecated"):
        legacy_spec = dataset_spec_to_generation_spec(spec)

    assert legacy_spec.seed == 11
    assert legacy_spec.table.columns[0].choices == ["new", "shipped"]
    assert legacy_spec.table.columns[1].min_value == 10.0
    assert legacy_spec.table.columns[1].max_value == 99.0
    assert legacy_spec.table.columns[2].min_datetime.isoformat() == "2024-01-01T00:00:00"
    assert legacy_spec.table.columns[2].max_datetime.isoformat() == "2024-12-31T23:59:59"


def test_json_loader_distinguishes_profiles_from_specs(tmp_path) -> None:
    profile_path = tmp_path / "profile.json"
    spec_path = tmp_path / "spec.json"

    profile_path.write_text(
        json.dumps(
            {
                "source_type": "csv",
                "entities": [{"name": "customers", "row_count": 1, "fields": [], "primary_key_candidates": []}],
            }
        )
    )
    spec_path.write_text(json.dumps({"entities": [{"name": "customers", "row_count": 1, "fields": []}]}))

    assert isinstance(load_profile_or_spec(profile_path), DatasetProfile)
    assert isinstance(load_profile_or_spec(spec_path), DatasetSpec)


def test_parquet_adapter_uses_schema_metadata(tmp_path) -> None:
    path = tmp_path / "customers.parquet"
    table = pa.table({"customer_id": [1, 2], "active": [True, False], "score": [1.5, 2.5]})
    pq.write_table(table, path)

    profile = dataset_profile_from_parquet(path)
    customers = profile.entity("customers")

    assert profile.source_type == "parquet"
    assert customers.row_count == 2
    assert customers.field("customer_id").is_identifier is True
    assert customers.field("active").data_type == "boolean"
    assert customers.field("score").data_type == "float"


def test_adapters_package_keeps_legacy_workflow_helpers_out_of_dataset_oriented_exports() -> None:
    assert not hasattr(adapters_package, "LegacyGenerationResult")
    assert not hasattr(adapters_package, "generation_spec_to_dataset_spec")
    assert not hasattr(adapters_package, "legacy_profile_to_dataset_profile")
    assert not hasattr(adapters_package, "legacy_profile_to_dataset_spec")
    assert not hasattr(adapters_package, "multi_table_generation_spec_to_dataset_spec")
    assert not hasattr(adapters_package, "dataset_spec_to_generation_spec")
    assert not hasattr(adapters_package, "generate_legacy_compatibility_result")
    assert not hasattr(adapters_package, "generate_legacy_rows")
    assert not hasattr(adapters_package, "legacy_profile_to_generation_spec")
    assert not hasattr(adapters_package, "load_legacy_generation_spec")
    assert not hasattr(adapters_package, "prepare_legacy_generation_spec")
    assert not hasattr(adapters_package, "validate_legacy_rows_file")
    assert not hasattr(adapters_package, "validate_legacy_rows_report")
