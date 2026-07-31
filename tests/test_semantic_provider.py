from __future__ import annotations

from typing import Any

import pytest

from test_data_agent.core.dataset import DatasetSpec
from test_data_agent.core.entity import EntitySpec
from test_data_agent.core.field import FieldSpec, FieldType
from test_data_agent.generation import (
    SemanticProviderError,
    SemanticValueRequest,
    generate_dataset,
)


class RecordingProvider:
    def __init__(self, value: Any) -> None:
        self.value = value
        self.requests: list[SemanticValueRequest] = []

    def generate(self, request: SemanticValueRequest) -> Any:
        self.requests.append(request)
        return self.value


def test_semantic_provider_receives_only_row_free_metadata() -> None:
    provider = RecordingProvider("north")
    spec = _spec(
        FieldSpec(
            name="region",
            data_type=FieldType.STRING,
            semantic_type="sales_region",
        )
    )

    first = generate_dataset(spec, seed=17, semantic_provider=provider)
    second = generate_dataset(spec, seed=17, semantic_provider=provider)

    assert first == second == {"accounts": [{"region": "north"}]}
    assert provider.requests[0] == SemanticValueRequest(
        entity_name="accounts",
        field_name="region",
        semantic_type="sales_region",
        data_type=FieldType.STRING,
        row_index=0,
        seed=17,
    )
    assert set(provider.requests[0].model_dump()) == {
        "schema_version",
        "entity_name",
        "field_name",
        "semantic_type",
        "data_type",
        "row_index",
        "seed",
    }


def test_semantic_provider_cannot_override_sensitive_generation() -> None:
    provider = RecordingProvider("attacker@example.com")
    spec = _spec(
        FieldSpec(
            name="email",
            data_type=FieldType.STRING,
            semantic_type="email",
            sensitive=True,
        )
    )

    rows = generate_dataset(spec, seed=17, semantic_provider=provider)

    assert provider.requests == []
    assert rows["accounts"][0]["email"].endswith("@example.test")


@pytest.mark.parametrize(
    ("value", "message"),
    [
        ("person@example.com", "sensitive data"),
        ("Bearer " + "synthetic-secret-token", "sensitive data"),
        (123, "wrong field type"),
        ("x" * 1025, "size limit"),
    ],
)
def test_semantic_provider_output_is_validated(value: Any, message: str) -> None:
    provider = RecordingProvider(value)
    spec = _spec(
        FieldSpec(
            name="region",
            data_type=FieldType.STRING,
            semantic_type="sales_region",
        )
    )

    with pytest.raises(SemanticProviderError, match=message):
        generate_dataset(spec, seed=17, semantic_provider=provider)


def test_semantic_provider_can_defer_to_builtin_generation() -> None:
    provider = RecordingProvider(None)
    spec = _spec(
        FieldSpec(
            name="region",
            data_type=FieldType.STRING,
            semantic_type="sales_region",
            distribution={"kind": "string_pattern", "min_length": 4, "max_length": 4},
        )
    )

    with_provider = generate_dataset(spec, seed=17, semantic_provider=provider)
    without_provider = generate_dataset(spec, seed=17)

    assert with_provider == without_provider


def _spec(field: FieldSpec) -> DatasetSpec:
    return DatasetSpec(
        entities=[
            EntitySpec(
                name="accounts",
                row_count=1,
                fields=[field],
            )
        ]
    )
