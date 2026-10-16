"""Every source supplies evidence to one reviewed contract and four output adapters."""

from __future__ import annotations

import csv
import json
from datetime import date, datetime
from decimal import Decimal

import pytest

from test_data_agent.adapters import (
    dataset_profile_from_csv_file,
    dataset_profile_from_csv_folder,
    dataset_profile_from_parquet,
    dataset_profile_from_trino_profile,
    load_json_dataset_profile,
)
from test_data_agent.core.dataset import DatasetProfile, DatasetSpec
from test_data_agent.core.field import FieldType
from test_data_agent.core.limits import GenerationBudget
from test_data_agent.core.settings import GenerationMode, OutputFormat
from test_data_agent.generation import generate_dataset
from test_data_agent.io.readers import load_dataset_rows, load_dataset_spec
from test_data_agent.io.workflows import (
    generate_dataset_bundle,
    generate_dataset_from_profile_artifacts,
)
from test_data_agent.io.writers import dataset_spec_to_yaml
from test_data_agent.postgres_config import PostgresConfig
from test_data_agent.postgres_profiler import PostgresProfiler
from test_data_agent.rules.typed_values import numeric_row
from test_data_agent.sql_query_source import (
    SqlQueryAdapter,
    SqlQueryProfileRequest,
    QuerySourceColumn,
    inspect_query_source,
    authorize_query_source,
)
from test_data_agent.sql_query_profiling import (
    profile_validated_query,
    QueryResultColumn,
)
from test_data_agent.validation import validate_dataset

SOURCES = (
    "csv",
    "csv_folder",
    "parquet",
    "json_profile",
    "trino",
    "postgres",
    "postgres_query",
    "trino_query",
    "yaml_spec",
    "json_spec",
)
COLUMNS = {
    "id": "bigint",
    "quantity": "bigint",
    "ratio": "double precision",
    "total": "decimal(12,2)",
    "active": "boolean",
    "label": "varchar",
    "day": "date",
    "at": "timestamp",
    "optional": "varchar",
}


def reviewed_spec() -> DatasetSpec:
    def field(name, data_type, distribution=None, **kwargs):
        return dict(
            name=name, data_type=data_type, distribution=distribution or {}, **kwargs
        )

    return DatasetSpec.model_validate(
        {
            "entities": [
                {
                    "name": "records",
                    "row_count": 4,
                    "primary_key": "id",
                    "fields": [
                        field(
                            "id",
                            "integer",
                            {"kind": "synthetic_identifier"},
                            is_identifier=True,
                        ),
                        field(
                            "quantity",
                            "integer",
                            {"kind": "numeric", "min_value": 2, "max_value": 4},
                        ),
                        field(
                            "ratio",
                            "float",
                            {"kind": "numeric", "min_value": 0.25, "max_value": 0.5},
                        ),
                        field(
                            "total",
                            "decimal",
                            {
                                "kind": "decimal_range",
                                "precision": 12,
                                "scale": 2,
                                "min": "0",
                                "max": "100",
                            },
                        ),
                        field(
                            "active", "boolean", {"kind": "boolean", "true_ratio": 1}
                        ),
                        field(
                            "label",
                            "string",
                            {"kind": "categorical", "categories": [{"value": "ready"}]},
                        ),
                        field(
                            "day",
                            "date",
                            {
                                "kind": "date_range",
                                "min": "2024-01-02",
                                "max": "2024-01-03",
                            },
                        ),
                        field(
                            "at",
                            "datetime",
                            {
                                "kind": "datetime_range",
                                "min": "2024-01-02T01:02:03",
                                "max": "2024-01-03T01:02:03",
                            },
                        ),
                        field("optional", "string", nullable=True, null_ratio=1),
                    ],
                }
            ],
            "generation_settings": {"seed": 17, "locale": "en_US"},
            "constraints": [
                {
                    "type": "formula",
                    "entity": "records",
                    "fields": ["total"],
                    "expression": "quantity * 2",
                    "confidence": 1,
                    "status": "confirmed",
                }
            ],
            "business_rules": {
                "field_rules": [
                    {"table": "records", "field": "active", "required": True}
                ],
                "row_rules": [
                    {
                        "type": "formula",
                        "table": "records",
                        "field": "total",
                        "expression": "quantity * 2",
                        "mode": "check",
                    },
                    {
                        "type": "conditional_required",
                        "table": "records",
                        "when": {"field": "active", "equals": True},
                        "required_fields": ["label"],
                    },
                    {
                        "type": "conditional_required",
                        "table": "records",
                        "when": {"field": "optional", "equals": None},
                        "required_fields": ["ratio"],
                    },
                ],
                "scenarios": [
                    {
                        "name": "ready",
                        "weight": 1,
                        "field_values": {"records": {"label": "ready"}},
                    }
                ],
            },
        }
    )


def aggregate(sql):
    if "min_temporal" in sql:
        value = datetime(2023, 2, 1) if '"at"' in sql else date(2023, 2, 1)
        return [
            {
                "row_count": 3,
                "non_null_count": 3,
                "distinct_count": 1,
                "min_temporal": value,
                "max_temporal": value,
            }
        ]
    # Fictional aggregate-only results: never return source rows or field values.
    return [
        {
            "row_count": 3,
            "non_null_count": 3,
            "distinct_count": 3,
            "has_negative": False,
            "has_positive": True,
            "max_abs_magnitude": 1,
            "true_count": 2,
            "false_count": 1,
        }
    ]


def source_profile(kind, root) -> DatasetProfile:
    root.mkdir()
    if kind in {"csv", "csv_folder", "json_profile", "parquet"}:
        source = root / "records.csv"
        with source.open("w", newline="") as handle:
            writer = csv.writer(handle)
            writer.writerow(COLUMNS)
            writer.writerows(
                [
                    [
                        index,
                        7,
                        0.75,
                        "2.50",
                        True,
                        "source-marker",
                        "2023-02-01",
                        "2023-02-01T00:00:00",
                        "",
                    ]
                    for index in (1, 2, 3)
                ]
            )
        if kind == "csv_folder":
            return dataset_profile_from_csv_folder(root, use_cache=False)
        if kind == "parquet":
            pa = pytest.importorskip("pyarrow")
            pq = pytest.importorskip("pyarrow.parquet")
            path = root / "records.parquet"
            pq.write_table(
                pa.Table.from_pylist(
                    [
                        dict(
                            id=1,
                            quantity=7,
                            ratio=0.75,
                            total=Decimal("2.50"),
                            active=True,
                            label="source-marker",
                            day=date(2023, 2, 1),
                            at=datetime(2023, 2, 1),
                            optional=None,
                        )
                    ]
                ),
                path,
            )
            return dataset_profile_from_parquet(path)
        profile = dataset_profile_from_csv_file(source)
        if kind == "json_profile":
            path = root / "saved-profile.json"
            path.write_text(profile.model_dump_json())
            return load_json_dataset_profile(path)
        return profile
    columns = [
        {
            "name": name,
            "data_type": dtype,
            "non_null_count": 3,
            "approx_distinct_count": 3,
        }
        for name, dtype in COLUMNS.items()
    ]
    if kind == "trino":
        return dataset_profile_from_trino_profile(
            {"table": "records", "row_count": 3, "columns": columns}
        )
    if kind == "postgres":
        config = PostgresConfig(
            source_id="warehouse",
            host="fictional.example.test",
            port=5432,
            database="fictional",
            user="reader",
            allowed_schemas=frozenset({"public"}),
            allowed_tables=frozenset({"public.records"}),
            allowed_columns=frozenset(f"public.records.{name}" for name in COLUMNS),
        )

        def fetch(query):
            if "c.relkind IN ('r', 'p')" in query.sql and "table_schema" in query.sql:
                return [{"table_schema": "public", "table_name": "records"}]
            if "pg_catalog.format_type" in query.sql:
                return [
                    {
                        "column_name": name,
                        "data_type": dtype,
                        "is_nullable": False,
                        "ordinal_position": index,
                    }
                    for index, (name, dtype) in enumerate(COLUMNS.items(), 1)
                ]
            if "con.contype" in query.sql:
                return []
            return aggregate(query.sql)

        return PostgresProfiler(config, fetch).profile()
    adapter = SqlQueryAdapter(kind.removesuffix("_query"))
    query = root / "query.sql"
    table = (
        "public.records" if adapter == SqlQueryAdapter.POSTGRES else "lake.safe.records"
    )
    query.write_text(f"SELECT {', '.join(COLUMNS)} FROM {table}")
    request = SqlQueryProfileRequest(
        adapter=adapter, source_id="warehouse", entity="records", query_file=query
    )
    metadata = tuple(
        QuerySourceColumn(name, dtype, False) for name, dtype in COLUMNS.items()
    )
    plan = authorize_query_source(inspect_query_source(request), metadata)
    return profile_validated_query(
        plan,
        describe_query=lambda query: tuple(
            QueryResultColumn(name, dtype, False) for name, dtype in COLUMNS.items()
        ),
        fetch_query=lambda query: aggregate(query.sql),
    )


@pytest.mark.parametrize("source", SOURCES)
@pytest.mark.parametrize("output", list(OutputFormat))
@pytest.mark.parametrize("mode", list(GenerationMode))
def test_source_output_matrix(tmp_path, source, output, mode):
    spec = reviewed_spec()
    profile = None
    if source.endswith("_spec"):
        path = tmp_path / (
            "reviewed.yaml" if source == "yaml_spec" else "reviewed.json"
        )
        path.write_text(
            dataset_spec_to_yaml(spec)
            if source == "yaml_spec"
            else spec.model_dump_json()
        )
        spec = load_dataset_spec(path)
    else:
        profile = source_profile(source, tmp_path / "source")
        assert profile.entities and len(profile.entities[0].fields) == len(COLUMNS)
        assert "source-marker" not in profile.model_dump_json()
        # An operator authors a complete spec from safe evidence. Source extrema and
        # raw categories do not become synthesis permissions or exact decimal bounds.
    assert {field.data_type for field in spec.entities[0].fields} == set(FieldType)
    spec.generation_settings.mode = mode
    spec.generation_settings.invalid_ratio = (
        1 if mode in {GenerationMode.NEGATIVE, GenerationMode.MIXED} else 0
    )
    spec.generation_settings.output_format = output
    target = tmp_path / "generated"
    result = generate_dataset_bundle(spec, output_folder=target, profile=profile)
    effective = load_dataset_spec(target / "dataset_spec.yaml")
    rows = load_dataset_rows(target)
    expected = generate_dataset(effective, seed=17)
    actual_normalized = [
        numeric_row(row, effective.entities[0], budget=GenerationBudget())
        for row in rows["records"]
    ]
    expected_normalized = [
        numeric_row(row, effective.entities[0], budget=GenerationBudget())
        for row in expected["records"]
    ]
    assert actual_normalized == expected_normalized
    revalidated = validate_dataset(rows, effective)
    assert revalidated.model_dump() == result.validation.model_dump()
    assert len(rows["records"]) == (40 if mode == GenerationMode.LOAD_TEST else 4)
    assert effective.business_rules == spec.business_rules
    manifest = json.loads((target / "generation_manifest.json").read_text())
    assert manifest["source_rows_copied"] is False
    assert (target / "profile.json").exists() == (profile is not None)


@pytest.mark.parametrize("output", list(OutputFormat))
def test_multi_entity_saved_profile_uses_common_bundle(tmp_path, output):
    from test_data_agent.core.entity import EntityProfile
    from test_data_agent.core.field import FieldProfile

    profile = DatasetProfile(
        source_type="json_profile",
        entities=[
            EntityProfile(
                name=name,
                row_count=2,
                fields=[FieldProfile(name="amount", data_type="integer")],
            )
            for name in ("first", "second")
        ],
    )
    target = tmp_path / "bundle"
    report, _ = generate_dataset_from_profile_artifacts(
        profile,
        count=3,
        seed=17,
        output_path=target,
        output_format=output,
        mode="load_test",
    )
    assert report.valid
    assert {name: len(rows) for name, rows in load_dataset_rows(target).items()} == {
        "first": 3,
        "second": 3,
    }
