"""Run-local distribution preparation preserves generation and validation."""

from collections import Counter
from typing import Any

import pytest

import test_data_agent.core.field as field_module
import test_data_agent.generation.entity_generator as generator
from test_data_agent.core.dataset import DatasetSpec
from test_data_agent.core.entity import EntitySpec
from test_data_agent.core.field import FieldSpec
from test_data_agent.generation.semantic_provider import SemanticValueRequest
from test_data_agent.io.writers import rows_to_csv
from test_data_agent.validation.schema_validator import validate_schema


def mixed_spec(mode: str = "valid") -> DatasetSpec:
    fields = [
        FieldSpec(name="id", data_type="integer", is_identifier=True),
        FieldSpec(name="group_id", data_type="string", is_identifier=True,
                  nullable=True, null_ratio=0.25,
                  distribution={"kind": "synthetic_identifier", "pool_size": 3}),
        FieldSpec(name="quantity", data_type="integer",
                  distribution={"kind": "numeric", "min_value": 1, "max_value": 40}),
        FieldSpec(name="amount", data_type="float",
                  distribution={"kind": "numeric_shape", "max_abs_magnitude": 2,
                                "has_negative": True, "has_positive": True}),
        FieldSpec(name="active", data_type="boolean",
                  distribution={"kind": "boolean", "true_ratio": 0.3}),
        FieldSpec(name="day", data_type="date",
                  distribution={"kind": "date_range", "min": "2020-01-01", "max": "2025-01-01"}),
        FieldSpec(name="instant", data_type="datetime",
                  distribution={"kind": "datetime_range", "min": "2024-01-01T00:00:00+03:00",
                                "max": "2024-01-03T00:00:00+03:00"}),
        FieldSpec(name="category", data_type="string",
                  distribution={"kind": "categorical", "categories": [
                      {"value": "synthetic_alpha", "count": 3},
                      {"value": "synthetic_beta", "count": 1}]}),
        FieldSpec(name="code", data_type="string", nullable=True, null_ratio=0.3,
                  semantic_type="fictional_code",
                  distribution={"kind": "string_pattern", "min_length": 16, "max_length": 24}),
        FieldSpec(name="untyped", data_type="string",
                  distribution={"kind": "string_pattern", "min_length": 12, "max_length": 12}),
        FieldSpec(name="email", data_type="string", sensitive=True, semantic_type="email"),
    ]
    return DatasetSpec(
        entities=[EntitySpec(name=name, row_count=20, primary_key="id",
                             fields=[field.model_copy(deep=True) for field in fields])
                  for name in ("events", "other_events")],
        generation_settings={"mode": mode, "invalid_ratio": 0.35 if mode in {"mixed", "negative"} else 0.0, "locale": "en_US"},
    )


class DeferringProvider:
    def __init__(self) -> None:
        self.requests: list[SemanticValueRequest] = []

    def generate(self, request: SemanticValueRequest) -> None:
        self.requests.append(request)
        return None


@pytest.mark.parametrize("mode", ["valid", "mixed", "negative"])
def test_preparation_preserves_seeded_rows_and_provider_requests(monkeypatch, mode):
    spec = mixed_spec(mode)
    original_spec = spec.model_dump(mode="json")
    prepared_provider = DeferringProvider()
    prepared = generator.generate_dataset(spec, seed=73, semantic_provider=prepared_provider)
    generate_row = generator.generate_row

    def uncached_row(*args: Any, **kwargs: Any) -> dict[str, Any]:
        kwargs.pop("distributions", None)
        return generate_row(*args, **kwargs)

    monkeypatch.setattr(generator, "generate_row", uncached_row)
    uncached_provider = DeferringProvider()
    uncached = generator.generate_dataset(spec, seed=73, semantic_provider=uncached_provider)

    assert prepared == uncached
    assert {name: rows_to_csv(rows) for name, rows in prepared.items()} == {
        name: rows_to_csv(rows) for name, rows in uncached.items()
    }
    assert prepared_provider.requests == uncached_provider.requests
    assert spec.model_dump(mode="json") == original_spec
    if mode != "negative":
        assert prepared_provider.requests
        assert any(row["group_id"] is None for row in prepared["events"])
        assert len({row["group_id"] for row in prepared["events"]
                    if row["group_id"] is not None}) == 3


def test_distribution_parse_work_is_bounded_by_fields(monkeypatch):
    # Released generation deep-copies specs and rereads mutable identifier metadata.
    # Non-identifier distribution preparation must still be independent of row count.
    calls: Counter[str] = Counter()
    parse_distribution = field_module.parse_distribution

    def tracked_parse(data):
        if data and data.get("kind") != "synthetic_identifier":
            calls[repr(sorted(data.items()))] += 1
        return parse_distribution(data)

    monkeypatch.setattr(field_module, "parse_distribution", tracked_parse)
    totals = []
    for row_count in (1, 50):
        calls.clear()
        spec = mixed_spec()
        for entity in spec.entities:
            entity.row_count = row_count
        generator.generate_dataset(spec, seed=73)
        totals.append(calls.copy())
    assert totals[0] and totals[0] == totals[1]


def test_generation_preparation_sees_nested_changes_between_calls():
    spec = DatasetSpec(entities=[EntitySpec(name="items", row_count=5, fields=[
        FieldSpec(name="quantity", data_type="integer",
                  distribution={"kind": "numeric", "min_value": 3, "max_value": 3}),
        FieldSpec(name="category", data_type="string", distribution={"kind": "categorical",
                  "categories": [{"value": "synthetic_before", "count": 1}]}),
    ])])
    first = generator.generate_dataset(spec, seed=73)["items"]
    quantity, category = spec.entities[0].fields
    quantity.distribution.update(min_value=7, max_value=7)
    category.distribution["categories"][0]["value"] = "synthetic_after"
    changed_spec = spec.model_dump(mode="json")
    second = generator.generate_dataset(spec, seed=73)["items"]

    assert first == [{"quantity": 3, "category": "synthetic_before"}] * 5
    assert second == [{"quantity": 7, "category": "synthetic_after"}] * 5
    assert spec.model_dump(mode="json") == changed_spec


def test_schema_preparation_sees_changed_lengths_and_field_types():
    spec = DatasetSpec(entities=[EntitySpec(name="items", row_count=1, fields=[
        FieldSpec(name="code", data_type="string",
                  distribution={"kind": "string_pattern", "min_length": 4, "max_length": 4}),
    ])])
    rows = {"items": [{"code": "abcd"}]}
    assert validate_schema(rows, spec) == []
    field = spec.entities[0].fields[0]
    field.distribution.update(min_length=8, max_length=8)
    assert validate_schema(rows, spec) == ["items[0].code has wrong length"]
    field.distribution = {}
    field.data_type = "integer"
    assert validate_schema(rows, spec) == ["items[0].code has wrong type"]
    assert rows == {"items": [{"code": "abcd"}]}
