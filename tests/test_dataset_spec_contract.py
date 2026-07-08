from test_data_agent.core import (
    CategoricalDistribution,
    DatasetSpec,
    GenerationMode,
    NumericDistribution,
    PrivacyAction,
    PrivacyClassification,
    ValidationSettings,
    infer_sensitive_from_name,
    mask_pattern,
    validate_distribution,
)
from test_data_agent.adapters import (
    csv_profile_to_dataset_profile,
    csv_profile_to_dataset_spec,
    generation_spec_to_dataset_spec,
    load_json_dataset_spec,
    multi_table_generation_spec_to_dataset_spec,
    parquet_file_to_dataset_profile,
    trino_profile_to_dataset_profile,
)
from test_data_agent.csv_profiler import profile_csv
from test_data_agent.core.entity import EntitySpec
from test_data_agent.core.field import FieldSpec, FieldType
from test_data_agent.spec import (
    ColumnSpec,
    DataType,
    ForeignKeySpec,
    GenerationSpec,
    GenerationStrategy,
    MultiTableGenerationSpec,
    OutputFormat,
    TableSpec,
)


def test_dataset_spec_loads_legacy_shape_with_default_settings() -> None:
    spec = DatasetSpec.model_validate(
        {
            "entities": [
                {
                    "name": "customers",
                    "row_count": 10,
                    "primary_key": "customer_id",
                    "fields": [
                        {
                            "name": "customer_id",
                            "data_type": "string",
                            "is_identifier": True,
                            "distribution": {"kind": "synthetic_identifier"},
                        }
                    ],
                }
            ],
            "relationships": [],
            "constraints": [],
        }
    )

    assert spec.entity("customers").primary_key == "customer_id"
    assert spec.privacy_rules == []
    assert spec.privacy_settings.treat_unknown_as_sensitive is True
    assert spec.generation_settings.mode == GenerationMode.VALID
    assert spec.validation_settings == ValidationSettings()


def test_dataset_spec_accepts_explicit_privacy_and_runtime_settings() -> None:
    spec = DatasetSpec.model_validate(
        {
            "entities": [
                EntitySpec(
                    name="customers",
                    row_count=1,
                    fields=[FieldSpec(name="email", data_type=FieldType.STRING, sensitive=True)],
                ).model_dump(mode="json")
            ],
            "privacy_rules": [
                {
                    "entity": "customers",
                    "field": "email",
                    "classification": "sensitive",
                    "action": "synthetic",
                    "semantic_type": "email",
                }
            ],
            "generation_settings": {
                "seed": 123,
                "mode": "mixed",
                "invalid_ratio": 0.1,
                "output_format": "csv",
            },
            "validation_settings": {"validate_privacy": True, "fail_fast": True},
        }
    )

    assert spec.privacy_rules[0].classification == PrivacyClassification.SENSITIVE
    assert spec.privacy_rules[0].action == PrivacyAction.SYNTHETIC
    assert spec.generation_settings.seed == 123
    assert spec.generation_settings.mode == GenerationMode.MIXED
    assert spec.generation_settings.invalid_ratio == 0.1
    assert spec.validation_settings.fail_fast is True


def test_typed_distribution_models_validate_known_shapes() -> None:
    numeric = validate_distribution({"kind": "numeric", "p05": 1, "p95": 10})
    categorical = validate_distribution(
        {
            "kind": "categorical",
            "categories": [
                {"value": "active", "count": 9},
                {"value": "paused", "count": 1},
            ],
        }
    )

    assert isinstance(numeric, NumericDistribution)
    assert numeric.p05 == 1
    assert numeric.p95 == 10
    assert isinstance(categorical, CategoricalDistribution)
    assert categorical.categories[0].value == "active"


def test_privacy_policy_is_shared_with_legacy_spec_module() -> None:
    from test_data_agent.spec import infer_sensitive_from_name as legacy_infer_sensitive

    assert legacy_infer_sensitive is infer_sensitive_from_name
    assert infer_sensitive_from_name("api_token") is True
    assert infer_sensitive_from_name("favorite_color") is False
    assert mask_pattern("alice@example.com", "email") == "email"
    assert mask_pattern("plain text", None) == "text_len_10"


def test_csv_adapter_normalizes_legacy_profile_into_dataset_shapes() -> None:
    fixture = __import__("pathlib").Path(__file__).parent / "fixtures" / "customers.csv"

    profile = profile_csv(fixture)
    dataset_profile = csv_profile_to_dataset_profile(profile)
    dataset_spec = csv_profile_to_dataset_spec(profile, count=12, seed=9)

    entity = dataset_profile.entity("customers")
    spec_entity = dataset_spec.entity("customers")
    email = entity.field("email")
    status = entity.field("status")

    assert dataset_profile.source_type == "csv"
    assert entity.primary_key_candidates == ["customer_id"]
    assert email.distribution["kind"] == "masked_patterns"
    assert status.distribution["kind"] == "categorical"
    assert spec_entity.row_count == 12
    assert dataset_spec.generation_settings.seed == 9


def test_legacy_generation_specs_normalize_into_dataset_spec() -> None:
    spec = GenerationSpec(
        seed=123,
        output_format=OutputFormat.CSV,
        table=TableSpec(
            name="customers",
            row_count=5,
            columns=[
                ColumnSpec(name="customer_id", data_type=DataType.STRING, strategy=GenerationStrategy.SEQUENCE),
                ColumnSpec(name="status", data_type=DataType.STRING, strategy=GenerationStrategy.CHOICE, choices=["active", "paused"]),
            ],
        ),
    )
    multi_spec = MultiTableGenerationSpec(
        seed=7,
        output_format=OutputFormat.JSON,
        tables=[
            TableSpec(
                name="customers",
                row_count=2,
                columns=[ColumnSpec(name="customer_id", data_type=DataType.STRING, strategy=GenerationStrategy.SEQUENCE)],
            ),
            TableSpec(
                name="orders",
                row_count=3,
                columns=[ColumnSpec(name="customer_id", data_type=DataType.STRING)],
            ),
        ],
        foreign_keys=[
            ForeignKeySpec(
                child_table="orders",
                child_field="customer_id",
                parent_table="customers",
                parent_field="customer_id",
            )
        ],
    )

    dataset_spec = generation_spec_to_dataset_spec(spec)
    multi_dataset_spec = multi_table_generation_spec_to_dataset_spec(multi_spec)

    assert dataset_spec.entity("customers").primary_key == "customer_id"
    assert dataset_spec.entity("customers").field("status").distribution["kind"] == "categorical"
    assert dataset_spec.generation_settings.output_format.value == "csv"
    assert multi_dataset_spec.relationships[0].parent_entity == "customers"
    assert multi_dataset_spec.relationships[0].child_entity == "orders"


def test_json_and_trino_adapters_load_legacy_profile_shapes(tmp_path) -> None:
    payload = {
        "source_type": "trino",
        "table": "accounts",
        "row_count": 4,
        "columns": [
            {
                "name": "account_id",
                "data_type": "integer",
                "nullable": False,
                "null_ratio": 0.0,
                "approx_distinct_count": 4,
                "sensitive": False,
                "top_values": [],
                "masked_patterns": [],
                "min_value": 1,
                "max_value": 4,
                "p05": 1,
                "p95": 4,
            }
        ],
    }
    path = tmp_path / "profile.json"
    path.write_text(__import__("json").dumps(payload))

    dataset_profile = trino_profile_to_dataset_profile(payload)
    dataset_spec = load_json_dataset_spec(path, count=6, seed=11)

    assert dataset_profile.source_type == "trino"
    assert dataset_profile.entity("accounts").primary_key_candidates == ["account_id"]
    assert dataset_spec.entity("accounts").row_count == 6
    assert dataset_spec.generation_settings.seed == 11


def test_parquet_adapter_reads_metadata_only(tmp_path) -> None:
    import pyarrow as pa
    import pyarrow.parquet as pq

    path = tmp_path / "events.parquet"
    pq.write_table(
        pa.table(
            {
                "event_id": [1, 2],
                "event_ts": ["2024-01-01T00:00:00", "2024-01-02T00:00:00"],
            }
        ),
        path,
    )

    dataset_profile = parquet_file_to_dataset_profile(path)

    assert dataset_profile.source_type == "parquet"
    assert dataset_profile.entity("events").row_count == 2
    assert [field.name for field in dataset_profile.entity("events").fields] == ["event_id", "event_ts"]
