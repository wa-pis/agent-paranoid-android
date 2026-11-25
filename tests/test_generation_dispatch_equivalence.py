"""Freeze generation dispatch while preserving random state and safety priority."""

from __future__ import annotations

from copy import deepcopy
import random
from types import MappingProxyType
from typing import Any, Callable

import pytest

from test_data_agent.core.dataset import DatasetProfile, DatasetSpec
from test_data_agent.core.entity import EntitySpec
from test_data_agent.core.field import FieldSpec, FieldType
from test_data_agent.core.limits import GenerationBudget
from test_data_agent.core.settings import GenerationMode
from test_data_agent.generation import infer_dataset_spec
import test_data_agent.generation.entity_generator as generator
from test_data_agent.generation.semantic_provider import SemanticValueRequest
from test_data_agent.generation.tiled_generator import TILE_ROWS, generate_tile
from test_data_agent.io.writers import rows_to_csv


def _previous_field_value(entity_name, field, row_index, rng, faker, seed, *, mode, invalid_ratio, semantic_provider=None, allow_null=True, identifier_domain=0, identifier_domain_count=1, resolved_distribution=False):
    if allow_null and field.nullable:
        if mode == generator.GenerationMode.EDGE:
            if field.null_ratio > 0 and row_index % 4 == 3:
                return None
        elif rng.random() < field.null_ratio:
            return None
    if generator.should_generate_invalid_value(field, rng, mode=mode, invalid_ratio=invalid_ratio):
        return generator.invalid_value_for_type(field.data_type)
    if field.is_identifier:
        return generator.synthetic_identifier(entity_name, field, row_index, seed, domain=identifier_domain, domain_count=identifier_domain_count)
    if field.sensitive and field.data_type == generator.FieldType.STRING:
        return generator.synthetic_sensitive_value(field, faker)
    if mode == generator.GenerationMode.EDGE:
        return generator.edge_field_value(field, row_index, rng)
    if semantic_provider is not None and field.data_type != generator.FieldType.DECIMAL and (field.semantic_type is not None) and (not generator.is_sensitive_field(field.name, field.semantic_type)):
        provider_value = generator.request_semantic_value(semantic_provider, generator.SemanticValueRequest(entity_name=entity_name, field_name=field.name, semantic_type=field.semantic_type, data_type=field.data_type, row_index=row_index, seed=seed))
        if provider_value is not None:
            return provider_value
    distribution = field.distribution or {}
    typed_distribution = field.typed_distribution if resolved_distribution is False else resolved_distribution
    if isinstance(typed_distribution, generator.CategoricalDistribution) and typed_distribution.categories:
        return generator.weighted_choice(typed_distribution.categories, rng)
    numeric_distribution = typed_distribution if isinstance(typed_distribution, generator.NumericDistribution) else None
    numeric_shape = typed_distribution if isinstance(typed_distribution, generator.NumericShapeDistribution) else None
    boolean_distribution = typed_distribution if isinstance(typed_distribution, generator.BooleanDistribution) else None
    date_distribution = typed_distribution if isinstance(typed_distribution, generator.DateRangeDistribution) else None
    datetime_distribution = typed_distribution if isinstance(typed_distribution, generator.DateTimeRangeDistribution) else None
    string_distribution = typed_distribution if isinstance(typed_distribution, generator.StringPatternDistribution) else None
    if field.data_type == generator.FieldType.INTEGER:
        return int(round(generator.ranged_number(numeric_distribution, numeric_shape, distribution, rng, default_min=0, default_max=1000)))
    if field.data_type == generator.FieldType.FLOAT:
        value = generator.ranged_number(numeric_distribution, numeric_shape, distribution, rng, default_min=0.0, default_max=1000.0)
        return value if numeric_shape is not None and numeric_shape.subunit_ratio else round(value, 6)
    if field.data_type == generator.FieldType.DECIMAL:
        assert isinstance(typed_distribution, generator.DecimalRangeDistribution)
        return generator.sample_decimal(rng, low=typed_distribution.min, high=typed_distribution.max, precision=typed_distribution.precision, scale=typed_distribution.scale)
    if field.data_type == generator.FieldType.BOOLEAN:
        return generator.boolean_value(boolean_distribution, distribution, rng)
    if field.data_type == generator.FieldType.DATE:
        return generator.ranged_datetime(date_distribution, distribution, rng, date_only=True)
    if field.data_type == generator.FieldType.DATETIME:
        return generator.ranged_datetime(datetime_distribution, distribution, rng, date_only=False)
    return generator.synthetic_string(field, string_distribution, rng)


def _outcome(function: Callable[[], Any]) -> tuple[Any, ...]:
    try:
        value = function()
        return "value", type(value), value
    except Exception as error:
        return "error", type(error), error.args


def _distributions() -> list[dict[str, Any]]:
    return [
        {},
        {"kind": "numeric", "min_value": -7, "max_value": 13, "p05": -3, "p95": 9,
         "scale_factor": 0.5},
        {"kind": "numeric", "min_value": 7, "max_value": 7},
        {"kind": "numeric_shape", "max_abs_magnitude": 2,
         "has_negative": True, "has_positive": True},
        {"kind": "boolean", "true_ratio": 0.3},
        {"kind": "date_range", "min": "2020-02-28", "max": "2024-03-01"},
        {"kind": "date_range"},
        {"kind": "datetime_range", "min": "2024-02-28T12:00:00+03:00",
         "max": "2024-03-01T13:00:00+03:00"},
        {"kind": "categorical", "categories": [
            {"value": "synthetic_alpha", "count": 0},
            {"value": "synthetic_beta", "count": 0.5},
            {"value": "synthetic_gamma", "count": 2.25}]},
        {"kind": "categorical", "categories": []},
        {"kind": "string_pattern", "min_length": 16, "max_length": 24},
        {"kind": "masked_patterns", "patterns": [{"pattern": "synthetic_XX", "count": 1}]},
        {"min_value": 3, "max_value": 7, "true_ratio": 0.25,
         "min": "2024-01-01T00:00:00+03:00", "max": "2024-01-03",
         "min_length": 4, "max_length": 8},
    ]


@pytest.mark.parametrize("data_type", list(FieldType))
@pytest.mark.parametrize("mode", list(GenerationMode))
def test_all_type_and_distribution_combinations_preserve_values_and_rng(data_type, mode):
    current_faker, previous_faker = generator.create_faker("en_US"), generator.create_faker("en_US")
    for distribution in (_distributions() if data_type != FieldType.DECIMAL else [{"kind": "decimal_range", "precision": 8, "scale": 2, "min": "-7.25", "max": "13.75"}]):
        field = FieldSpec.model_construct(name="payload", data_type=data_type, nullable=True, null_ratio=0.25,
                          distribution=deepcopy(distribution))
        original = field.model_dump(mode="json")
        for prepared in (False, True):
            metadata = MappingProxyType({field.name: field.typed_distribution}) if prepared else None
            current_rng, previous_rng = random.Random(73), random.Random(73)
            current_faker.seed_instance(71)
            previous_faker.seed_instance(71)
            for row_index in range(12):
                kwargs = {"mode": mode, "invalid_ratio": 0.35, "resolved_distribution": metadata[field.name] if prepared else False}
                assert _outcome(lambda: generator.generate_field_value(
                    "fictional", field, row_index, current_rng, current_faker, 73, **kwargs,
                )) == _outcome(lambda: _previous_field_value(
                    "fictional", field, row_index, previous_rng, previous_faker, 73, **kwargs,
                )), (distribution, prepared, row_index)
                assert current_rng.getstate() == previous_rng.getstate()
                assert current_faker.random.getstate() == previous_faker.random.getstate()
            assert field.model_dump(mode="json") == original


@pytest.mark.parametrize("data_type,distribution,nullable", [
    ("integer", {"min_value": "synthetic_invalid_number"}, False),
    ("float", {"min_value": "synthetic_invalid_number"}, False),
    ("boolean", {"true_ratio": "synthetic_invalid_ratio"}, False),
    ("string", {"min_length": "synthetic_invalid_length"}, False),
    ("string", {"kind": "string_pattern", "min_length": 0, "max_length": 0}, False),
    ("string", {"kind": "string_pattern", "min_length": 0, "max_length": 0}, True),
])
def test_dispatch_keeps_fallback_errors_and_zero_length_behavior(data_type, distribution, nullable):
    field = FieldSpec.model_construct(name="payload", data_type=data_type, distribution=distribution, nullable=nullable)
    states, outcomes = [], []
    for function in (generator.generate_field_value, _previous_field_value):
        rng, faker = random.Random(73), generator.create_faker("en_US")
        faker.seed_instance(71)
        outcomes.append(_outcome(lambda: function(
            "fictional", field, 0, rng, faker, 73, mode=GenerationMode.VALID, invalid_ratio=0,
        )))
        states.append((rng.getstate(), faker.random.getstate()))
    assert outcomes[0] == outcomes[1]
    assert states[0] == states[1]
    assert outcomes[0][0] == ("value" if nullable else "error")


class _Provider:
    def __init__(self, value):
        self.value = value
        self.requests: list[SemanticValueRequest] = []

    def generate(self, request):
        self.requests.append(request)
        return self.value


@pytest.mark.parametrize("case", [
    "null", "primary_key", "identifier", "sensitive", "sensitive_name", "negative",
    "provider", "provider_defer", "provider_reject",
])
def test_nullable_invalid_identifier_sensitive_and_provider_priority(case):
    field = FieldSpec(name="payload", data_type="string", semantic_type="fictional_code",
                      distribution={"kind": "categorical", "categories": [
                          {"value": "synthetic_category", "count": 1}]})
    mode, allow_null, provider_value = GenerationMode.VALID, True, "synthetic_provider"
    if case in {"null", "primary_key"}:
        field.nullable, field.null_ratio = True, 1
        allow_null = case != "primary_key"
    elif case == "identifier":
        field.is_identifier = True
        field.distribution = {"kind": "synthetic_identifier", "pool_size": 3}
    elif case == "sensitive":
        field.sensitive, field.semantic_type = True, "email"
    elif case == "sensitive_name":
        field.name, field.semantic_type = "phone", "phone"
    elif case == "negative":
        mode = GenerationMode.NEGATIVE
    elif case == "provider_defer":
        provider_value = None
    elif case == "provider_reject":
        provider_value = "synthetic_canary@invalid.example"
    observations = []
    for function in (generator.generate_field_value, _previous_field_value):
        rng, faker = random.Random(73), generator.create_faker("en_US")
        faker.seed_instance(71)
        provider = _Provider(provider_value)
        outcome = _outcome(lambda: function(
            "fictional", field, 5, rng, faker, 73, mode=mode, invalid_ratio=0.35,
            allow_null=allow_null, semantic_provider=provider, identifier_domain=2,
            identifier_domain_count=4,
            resolved_distribution=field.typed_distribution,
        ))
        observations.append((outcome, rng.getstate(), faker.random.getstate(), provider.requests))
    assert observations[0] == observations[1]
    assert len(observations[0][3]) == (2 if case in {
        "primary_key", "provider", "provider_defer", "provider_reject",
    } else 0)
    if case == "provider_reject":
        assert observations[0][0][0] == "error"
        assert observations[0][0][2] == ("semantic provider returned sensitive data",)


def _spec(mode=GenerationMode.VALID):
    fields = [
        FieldSpec(name="id", data_type="integer", is_identifier=True),
        FieldSpec(name="amount", data_type="float", distribution={
            "kind": "numeric", "min_value": -7, "max_value": 13, "scale_factor": 0.5}),
        FieldSpec(name="count", data_type="integer", distribution={
            "kind": "numeric_shape", "max_abs_magnitude": 2,
            "has_negative": True, "has_positive": True}),
        FieldSpec(name="active", data_type="boolean", nullable=True, null_ratio=0.3,
                  distribution={"kind": "boolean", "true_ratio": 0.3}),
        FieldSpec(name="day", data_type="date", distribution={
            "kind": "date_range", "min": "2020-01-01", "max": "2025-01-01"}),
        FieldSpec(name="instant", data_type="datetime", distribution={
            "kind": "datetime_range", "min": "2024-01-01T00:00:00+03:00",
            "max": "2024-01-03T00:00:00+03:00"}),
        FieldSpec(name="category", data_type="string", distribution={
            "kind": "categorical", "categories": [
                {"value": "synthetic_alpha", "count": 3},
                {"value": "synthetic_beta", "count": 1}]}),
        FieldSpec(name="code", data_type="string", nullable=True, null_ratio=0.2,
                  distribution={"kind": "string_pattern", "min_length": 16, "max_length": 24}),
        FieldSpec(name="email", data_type="string", sensitive=True, semantic_type="email"),
    ]
    return DatasetSpec(entities=[EntitySpec(name=name, row_count=17, primary_key="id",
                                           fields=deepcopy(fields)) for name in ("first", "second")],
                       generation_settings={"mode": mode, "invalid_ratio": 0.35 if mode in {"mixed", "negative"} else 0.0, "locale": "en_US"})


@pytest.mark.parametrize("mode", list(GenerationMode))
def test_complete_legacy_and_tiled_generation_match_frozen_dispatch(monkeypatch, mode):
    spec = _spec(mode)
    original = spec.model_dump(mode="json")
    current = generator.generate_dataset(spec, seed=73)
    current_tiles = [generate_tile(spec, index, 0, 73, budget=GenerationBudget())
                     for index in range(2)]
    for entity in spec.entities:
        entity.row_count = TILE_ROWS + 7
    current_tails = [generate_tile(spec, index, TILE_ROWS, 73, budget=GenerationBudget())
                     for index in range(2)]
    monkeypatch.setattr(generator, "generate_field_value", _previous_field_value)
    previous_tails = [generate_tile(spec, index, TILE_ROWS, 73, budget=GenerationBudget())
                      for index in range(2)]
    for entity in spec.entities:
        entity.row_count = 17
    previous = generator.generate_dataset(spec, seed=73)
    previous_tiles = [generate_tile(spec, index, 0, 73, budget=GenerationBudget())
                      for index in range(2)]
    assert current == previous
    assert current_tiles == previous_tiles
    assert current_tails == previous_tails
    for name in current:
        assert rows_to_csv(current[name]) == rows_to_csv(previous[name])
    for before, after in zip(previous_tiles + previous_tails, current_tiles + current_tails):
        assert rows_to_csv(before) == rows_to_csv(after)
    assert spec.model_dump(mode="json") == original


def test_generation_observes_nested_distribution_and_type_edits_between_calls(monkeypatch):
    spec = DatasetSpec(entities=[EntitySpec(name="fictional", row_count=4, fields=[
        FieldSpec(name="payload", data_type="integer", distribution={
            "kind": "numeric", "min_value": 3, "max_value": 3}),
    ])])
    current_function = generator.generate_field_value
    for data_type, distribution, expected in [
        ("integer", {"kind": "numeric", "min_value": 3, "max_value": 3}, 3),
        ("integer", {"kind": "numeric", "min_value": 7, "max_value": 7}, 7),
        ("string", {"kind": "categorical", "categories": [
            {"value": "synthetic_changed", "count": 1}]}, "synthetic_changed"),
    ]:
        field = spec.entities[0].fields[0]
        field.data_type = data_type
        field.distribution.clear()
        field.distribution.update(distribution)
        original = spec.model_dump(mode="json")
        monkeypatch.setattr(generator, "generate_field_value", current_function)
        current = generator.generate_dataset(spec, seed=73)
        monkeypatch.setattr(generator, "generate_field_value", _previous_field_value)
        assert current == generator.generate_dataset(spec, seed=73)
        assert current == {"fictional": [{"payload": expected}] * 4}
        assert spec.model_dump(mode="json") == original


@pytest.mark.parametrize("source_type", [
    "csv", "csv_folder", "parquet", "json_profile", "legacy_profile", "postgres",
    "postgres_query", "trino", "trino_query", "custom_source",
])
def test_source_inferred_specs_share_generation_dispatch_and_privacy(monkeypatch, source_type):
    profile = DatasetProfile.model_validate({"source_type": source_type, "has_unmodeled_expressions": False, "entities": [{
        "name": "fictional", "row_count": 3, "fields": [
            {"name": data_type.value, "data_type": data_type} for data_type in FieldType if data_type != FieldType.DECIMAL
        ] + [{"name": "email", "data_type": "string", "sensitive": True, "semantic_type": "email"}],
    }]})
    spec = infer_dataset_spec(profile, count=3)
    original = spec.model_dump(mode="json")
    current = generator.generate_dataset(spec, seed=42)
    monkeypatch.setattr(generator, "generate_field_value", _previous_field_value)
    previous = generator.generate_dataset(spec, seed=42)
    assert current == previous
    assert rows_to_csv(current["fictional"]) == rows_to_csv(previous["fictional"])
    assert all(row["email"].endswith("@example.test") for row in current["fictional"])
    assert spec.model_dump(mode="json") == original
