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
from test_data_agent.core.entity import EntitySpec
from test_data_agent.core.field import FieldSpec, FieldType


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
