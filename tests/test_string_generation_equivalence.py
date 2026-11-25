"""Freeze string construction, random state and exceptional draw behavior."""

from __future__ import annotations

from copy import deepcopy
import random

import pytest

from test_data_agent.core.dataset import DatasetProfile, DatasetSpec
from test_data_agent.core.entity import EntitySpec
from test_data_agent.core.field import FieldSpec, FieldType
from test_data_agent.core.limits import GenerationBudget
from test_data_agent.core.settings import GenerationMode
from test_data_agent.generation import infer_dataset_spec
import test_data_agent.generation.entity_generator as generator
from test_data_agent.generation.tiled_generator import TILE_ROWS, generate_tile
from test_data_agent.io.writers import rows_to_csv


def _previous_string(field, typed_distribution, rng):
    # Freeze the whole old helper, including the generator's PEP 479 boundary.
    distribution = field.distribution or {}
    if typed_distribution is not None:
        min_length = typed_distribution.min_length
        max_length = typed_distribution.max_length
    else:
        min_length = int(distribution.get("min_length", 6))
        max_length = int(distribution.get("max_length", max(min_length, 12)))
    if max_length > generator.max_input_cell_chars():
        raise generator.GenerationLimitError("generated string exceeds configured cell size limit")
    if max_length == 0:
        if field.nullable:
            return ""
        raise ValueError("required string field cannot have zero maximum length")
    length = rng.randint(max(1, min_length), max_length)
    prefix = (generator.SYNTHETIC_PREFIX if length >= len(generator.SYNTHETIC_PREFIX) + 6
              else ("syn_" if length >= 10 else ""))
    return prefix + "".join(
        rng.choice(generator.string.ascii_lowercase) for _ in range(length - len(prefix))
    )


def _exception(error):
    return (type(error), error.args, _exception(error.__cause__) if error.__cause__ else None,
            _exception(error.__context__) if error.__context__ else None,
            error.__suppress_context__)


def _outcome(call):
    try:
        value = call()
        return "value", type(value), value
    except BaseException as error:
        return "error", _exception(error)


@pytest.mark.parametrize("bounds", [(value, value) for value in (0, 1, 6, 9, 10, 15, 16, 17, 24)]
                         + [(0, 24), (6, 17), (16, 24)])
@pytest.mark.parametrize("typed", [False, True])
@pytest.mark.parametrize("nullable", [False, True])
def test_length_boundaries_and_prepared_or_raw_metadata_match_values_states_and_errors(
    bounds, typed, nullable,
):
    low, high = bounds
    distribution = {"min_length": low, "max_length": high}
    if typed:
        distribution["kind"] = "string_pattern"
    field = FieldSpec.model_construct(name="payload", data_type=FieldType.STRING, nullable=nullable,
                      distribution=distribution)
    before = field.model_dump(mode="json")
    metadata = field.typed_distribution if typed else None
    for seed in (0, 42, 73):
        current, previous = random.Random(seed), random.Random(seed)
        for _ in range(8):
            assert _outcome(lambda: generator.synthetic_string(field, metadata, current)) == _outcome(
                lambda: _previous_string(field, metadata, previous))
            assert current.getstate() == previous.getstate()
    assert field.model_dump(mode="json") == before


@pytest.mark.parametrize("distribution", [
    {"min_length": "synthetic_invalid_length"},
    {"max_length": "synthetic_invalid_length"},
    {"min_length": 7, "max_length": 3},
])
def test_raw_length_errors_preserve_exception_and_random_state(distribution):
    field = FieldSpec.model_construct(name="payload", data_type=FieldType.STRING, distribution=distribution)
    results = []
    for function in (generator.synthetic_string, _previous_string):
        rng = random.Random(42)
        results.append((_outcome(lambda: function(field, None, rng)), rng.getstate()))
    assert results[0] == results[1]
    assert results[0][0][0] == "error"


class _ChangingRandom(random.Random):
    def __init__(self, case, change_alphabet):
        super().__init__(73)
        self.case = case
        self.change_alphabet = change_alphabet
        self.trace: list[tuple[str, str]] = []
        self.choice_lookups = 0

    def __getattribute__(self, name):
        if name == "choice":
            state = object.__getattribute__(self, "__dict__")
            state["choice_lookups"] += 1
        return super().__getattribute__(name)

    def randint(self, low, high):
        if self.case == "randint_stop":
            raise StopIteration("synthetic length stop")
        return super().randint(low, high)

    def following_choice(self, alphabet):
        self.trace.append(("following", alphabet))
        return super().choice(alphabet)

    def choice(self, alphabet):
        self.trace.append(("choice", alphabet))
        if self.case == "replace" and len(self.trace) == 1:
            self.choice = self.following_choice
        if self.case == "alphabet" and len(self.trace) == 1:
            self.change_alphabet()
        if len(self.trace) == 3:
            if self.case == "stop":
                raise StopIteration("synthetic character stop")
            if self.case == "async_stop":
                raise StopAsyncIteration("synthetic character async stop")
            if self.case == "error":
                raise ValueError("synthetic character failure")
            if self.case == "interrupt":
                raise KeyboardInterrupt("synthetic character interrupt")
        value = super().choice(alphabet)
        return 12345 if self.case == "bad_return" and len(self.trace) == 1 else value


@pytest.mark.parametrize("case", [
    "replace", "alphabet", "stop", "async_stop", "error", "interrupt", "bad_return", "randint_stop",
])
def test_dynamic_draw_lookup_order_and_exception_chains_match(monkeypatch, case):
    field = FieldSpec(name="payload", data_type="string", distribution={
        "kind": "string_pattern", "min_length": 24, "max_length": 24})
    original_alphabet = generator.string.ascii_lowercase
    observed = []
    for function in (generator.synthetic_string, _previous_string):
        monkeypatch.setattr(generator.string, "ascii_lowercase", original_alphabet)
        rng = _ChangingRandom(case, lambda: monkeypatch.setattr(
            generator.string, "ascii_lowercase", "xyz"))
        outcome = _outcome(lambda: function(field, field.typed_distribution, rng))
        observed.append((outcome, rng.getstate(), rng.trace, rng.choice_lookups))
    assert observed[0] == observed[1]
    outcome, _, trace, lookups = observed[0]
    assert lookups == len(trace)
    if case == "replace":
        assert trace[0][0] == "choice" and all(item[0] == "following" for item in trace[1:])
    if case == "alphabet":
        assert trace[0][1] == original_alphabet and all(item[1] == "xyz" for item in trace[1:])
    if case == "stop":
        assert outcome[1][0] is RuntimeError
        assert outcome[1][1] == ("generator raised StopIteration",)
        assert outcome[1][2][0] is StopIteration
        assert outcome[1][2] == outcome[1][3] and outcome[1][4]
    if case == "randint_stop":
        assert outcome[1][0] is StopIteration and not trace
    if case == "bad_return":
        assert len(trace) == 24 - len(generator.SYNTHETIC_PREFIX)


def _spec(mode):
    return DatasetSpec(entities=[EntitySpec(name="fictional", row_count=17, primary_key="id", fields=[
        FieldSpec(name="id", data_type="integer", is_identifier=True),
        FieldSpec(name="small", data_type="string", distribution={"kind": "string_pattern", "min_length": 6, "max_length": 12}),
        FieldSpec(name="payload", data_type="string", nullable=True, null_ratio=0.3,
                  distribution={"kind": "string_pattern", "min_length": 16, "max_length": 24}),
        FieldSpec(name="quantity", data_type="integer", distribution={
            "kind": "numeric", "min_value": 1, "max_value": 40}),
        FieldSpec(name="email", data_type="string", sensitive=True, semantic_type="email"),
    ])], generation_settings={"mode": mode, "invalid_ratio": 0.35 if mode in {"mixed", "negative"} else 0.0, "locale": "en_US"})


@pytest.mark.parametrize("mode", list(GenerationMode))
def test_all_modes_legacy_tile_head_tail_csv_and_rng_faker_states_match(monkeypatch, mode):
    spec = _spec(mode)
    original = spec.model_dump(mode="json")
    actual = generator.synthetic_string
    observations = []
    for function in (actual, _previous_string):
        monkeypatch.setattr(generator, "synthetic_string", function)
        rng, faker = random.Random(73), generator.create_faker("en_US")
        faker.seed_instance(71)
        entity = spec.entities[0]
        distributions = [field.typed_distribution for field in entity.fields]
        direct = [generator.generate_row(entity, index, rng, faker, 73, mode=mode,
                                        invalid_ratio=0.35, distributions=distributions)
                  for index in range(17)]
        legacy = generator.generate_dataset(spec, seed=73)
        head = generate_tile(spec, 0, 0, 73, budget=GenerationBudget())
        entity.row_count = TILE_ROWS + 7
        tail = generate_tile(spec, 0, TILE_ROWS, 73, budget=GenerationBudget())
        entity.row_count = 17
        observations.append((direct, rng.getstate(), faker.random.getstate(), legacy, head, tail))
    assert observations[0] == observations[1]
    for index in (0, 4, 5):
        assert rows_to_csv(observations[0][index]) == rows_to_csv(observations[1][index])
    assert rows_to_csv(observations[0][3]["fictional"]) == rows_to_csv(observations[1][3]["fictional"])
    assert spec.model_dump(mode="json") == original


def test_nested_length_edits_between_calls_are_observed(monkeypatch):
    spec = _spec(GenerationMode.VALID)
    current = generator.synthetic_string
    for length in (6, 10, 16, 24):
        field = spec.entities[0].fields[2]
        field.distribution.update(min_length=length, max_length=length)
        original = deepcopy(spec.model_dump(mode="json"))
        monkeypatch.setattr(generator, "synthetic_string", current)
        actual = generator.generate_dataset(spec, seed=73)
        monkeypatch.setattr(generator, "synthetic_string", _previous_string)
        assert actual == generator.generate_dataset(spec, seed=73)
        assert all(row["payload"] is None or len(row["payload"]) == length for row in actual["fictional"])
        assert spec.model_dump(mode="json") == original


@pytest.mark.parametrize("source_type", [
    "csv", "csv_folder", "parquet", "json_profile", "legacy_profile", "postgres",
    "postgres_query", "trino", "trino_query", "custom_source",
])
def test_source_inferred_strings_keep_shared_privacy_and_bytes(monkeypatch, source_type):
    profile = DatasetProfile.model_validate({"source_type": source_type, "has_unmodeled_expressions": False, "entities": [{
        "name": "fictional", "row_count": 4, "fields": [
            {"name": "payload", "data_type": "string", "distribution": {
                "kind": "string_pattern", "min_length": 16, "max_length": 24}},
            {"name": "email", "data_type": "string", "sensitive": True, "semantic_type": "email"},
        ],
    }]})
    spec = infer_dataset_spec(profile, count=4)
    original = spec.model_dump(mode="json")
    actual = generator.generate_dataset(spec, seed=42)
    monkeypatch.setattr(generator, "synthetic_string", _previous_string)
    previous = generator.generate_dataset(spec, seed=42)
    assert actual == previous
    assert rows_to_csv(actual["fictional"]) == rows_to_csv(previous["fictional"])
    assert all(row["email"].endswith("@example.test") for row in actual["fictional"])
    assert spec.model_dump(mode="json") == original
