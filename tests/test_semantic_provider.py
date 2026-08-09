from __future__ import annotations

import threading
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
from test_data_agent.generation.semantic_provider import request_semantic_value


class RecordingProvider:
    def __init__(self, value: Any) -> None:
        self.value = value
        self.requests: list[SemanticValueRequest] = []

    def generate(self, request: SemanticValueRequest) -> Any:
        self.requests.append(request)
        return self.value


def test_semantic_provider_receives_only_row_free_metadata() -> None:
    provider = RecordingProvider("synthetic_north")
    spec = _spec(
        FieldSpec(
            name="region",
            data_type=FieldType.STRING,
            semantic_type="sales_region",
        )
    )

    first = generate_dataset(spec, seed=17, semantic_provider=provider)
    second = generate_dataset(spec, seed=17, semantic_provider=provider)

    assert first == second == {"accounts": [{"region": "synthetic_north"}]}
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


def test_semantic_provider_timeout_is_bounded_and_discards_output() -> None:
    release = threading.Event()

    class BlockingProvider:
        def generate(self, request: SemanticValueRequest) -> str:
            release.wait()
            return "synthetic_late"

    try:
        with pytest.raises(SemanticProviderError, match="timed out"):
            request_semantic_value(
                BlockingProvider(),
                _request(),
                timeout_seconds=0.01,
            )
    finally:
        release.set()


def test_semantic_provider_rejects_non_reproducible_output() -> None:
    values = iter(("synthetic_north", "synthetic_south"))

    class ChangingProvider:
        def generate(self, request: SemanticValueRequest) -> str:
            return next(values)

    with pytest.raises(SemanticProviderError, match="not reproducible"):
        request_semantic_value(ChangingProvider(), _request())


@pytest.mark.parametrize("value", ["Jane Doe", "14 Elm Crescent", "north"])
def test_semantic_provider_requires_synthetic_string_namespace(value: str) -> None:
    with pytest.raises(SemanticProviderError, match="synthetic namespace"):
        request_semantic_value(RecordingProvider(value), _request())


def _request() -> SemanticValueRequest:
    return SemanticValueRequest(
        entity_name="accounts",
        field_name="region",
        semantic_type="sales_region",
        data_type=FieldType.STRING,
        row_index=0,
        seed=17,
    )


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
