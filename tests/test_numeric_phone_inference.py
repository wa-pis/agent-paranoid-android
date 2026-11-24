"""Numeric profile semantics must not become phone generation instructions."""

import csv
import json
from collections.abc import Iterator
from pathlib import Path

import pytest

from test_data_agent.adapters import csv_profile_to_dataset_spec
from test_data_agent.core.field import FieldProfile
from test_data_agent.csv_profiler import (
    CSVColumnAccumulator,
    CSVColumnProfile,
    profile_column,
    profile_csv,
)
from test_data_agent.generation import generate_dataset, infer_dataset_spec
from test_data_agent.profiling import profile_example_folder
from test_data_agent.profiling.cache import (
    PROFILE_CACHE_FORMAT_VERSION,
    cache_path,
    csv_folder_fingerprint,
    load_cached_profile,
)
from test_data_agent.profiling.schema_profiler import FieldAccumulator, profile_field
from test_data_agent.validation import validate_dataset


def _profile_views(name: str, values: list[str]) -> Iterator[CSVColumnProfile | FieldProfile]:
    yield profile_column(name, values, len(values))
    yield profile_field(name, values, len(values))
    single = CSVColumnAccumulator(name)
    folder = FieldAccumulator(name)
    for value in values:
        single.add(value)
        folder.add(value)
    yield single.to_profile(len(values))
    yield folder.to_profile(len(values))


@pytest.mark.parametrize("values,data_type,sensitive", [
    (["3583770", "35837700", "3583770000", "358377000000"], "integer", True),
    (["35837700.25", "35837701.25"], "float", True),
    (["35837700.0", "35837701.0"], "float", True),
    (["-358377000000.0", "-358377000001.0"], "float", True),
    (["3.58377e7", "3.58378e7"], "float", True),
    (["-358377000000.25", "-358377000001.25"], "float", False),
], ids=["integers", "fractions", "integral_decimals", "negative_integral", "exponents", "negative_fractions"])
def test_numeric_values_keep_numeric_semantics_without_releasing_ambiguous_bounds(
    values: list[str], data_type: str, sensitive: bool,
) -> None:
    for profile in _profile_views("quantity", values):
        assert profile.data_type == data_type
        assert profile.semantic_type is None
        assert profile.sensitive is sensitive
        assert "phone" not in profile.model_dump_json()
        if sensitive:
            assert all(value not in profile.model_dump_json() for value in values)
            if isinstance(profile, CSVColumnProfile):
                assert profile.top_values == []
                assert profile.masked_patterns
                assert all(getattr(profile, key) is None for key in (
                    "min_value", "max_value", "p05", "p95",
                ))
            else:
                assert not {"min", "max", "p05", "p95"}.intersection(profile.distribution)


@pytest.mark.parametrize("name,values", [
    ("phone", ["12025550100", "12025550101"]),
    ("value", ["+1-202-555-0100", "+1-202-555-0101"]),
], ids=["explicit_phone_name", "formatted_phone_content"])
def test_phone_context_is_preserved(name: str, values: list[str]) -> None:
    for profile in _profile_views(name, values):
        assert profile.semantic_type == "phone"
        assert profile.sensitive
        assert profile.data_type in {"phone", "string"}
        assert all(value not in profile.model_dump_json() for value in values)


@pytest.mark.parametrize("value,semantic_type", [
    ("000" + "000" + "000", None),
    ("000-" + "00-" + "0000", "ssn"),
    ("9.12345678e8", None),
    ("42424242" + "42424242", None),
    ("sk" + "_test_" + "A1b2C3d4E5f6", "secret"),
], ids=["compact_ssn", "formatted_ssn", "exponent_ssn", "luhn_card", "secret"])
def test_numeric_inference_preserves_privacy_and_contextual_semantics(
    value: str, semantic_type: str | None,
) -> None:
    for profile in _profile_views("quantity", [value]):
        assert profile.sensitive
        assert profile.semantic_type == semantic_type
        assert value not in profile.model_dump_json()
        if isinstance(profile, CSVColumnProfile):
            assert profile.min_value is None
            assert profile.max_value is None
            assert profile.top_values == []


@pytest.mark.parametrize("late_value,semantic_type", [
    ("+1-202-555-0100", None),
    ("sk" + "_test_" + "A1b2C3d4E5f6", "secret"),
], ids=["late_phone", "late_secret"])
def test_sensitive_evidence_after_semantic_sample_still_masks_the_field(
    late_value: str, semantic_type: str | None,
) -> None:
    values = ["-358377000000.25"] * 101 + [late_value]
    for profile in _profile_views("quantity", values):
        assert profile.sensitive
        assert profile.semantic_type == semantic_type
        assert late_value not in profile.model_dump_json()
        if isinstance(profile, CSVColumnProfile):
            assert profile.min_value is None
            assert profile.max_value is None


def test_public_numeric_profiles_generate_numbers_deterministically(tmp_path: Path) -> None:
    source = tmp_path / "measurements.csv"
    values = [["35837700", "35837700.25"], ["35837701", "35837701.25"]]
    with source.open("w", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["quantity", "amount"])
        writer.writerows(values)

    single = profile_csv(source)
    folder = profile_example_folder(tmp_path, cache_dir=None)
    specs = (
        csv_profile_to_dataset_spec(single, seed=42, count=8),
        infer_dataset_spec(folder, count=8),
    )
    for profile in (single, folder):
        assert all(value not in profile.model_dump_json() for row in values for value in row)
    for spec in specs:
        entity = spec.entity("measurements")
        assert entity.field("quantity").data_type == "integer"
        assert entity.field("amount").data_type == "float"
        assert all(field.semantic_type is None for field in entity.fields)
        assert all(value not in spec.model_dump_json() for row in values for value in row)
        rows = generate_dataset(spec, seed=42)
        assert rows == generate_dataset(spec, seed=42)
        assert all(type(row["quantity"]) is int and type(row["amount"]) is float
                   for row in rows["measurements"])
        assert validate_dataset(rows, spec).valid


@pytest.mark.parametrize("cached_version", [5, 6, 7, 8])
def test_old_phone_inference_cache_is_recomputed(tmp_path: Path, cached_version: int) -> None:
    source = tmp_path / "source"
    source.mkdir()
    (source / "measurements.csv").write_text("quantity\n35837700\n35837701\n")
    cache_dir = tmp_path / "cache"
    cache_dir.mkdir()
    fingerprint = csv_folder_fingerprint(source)
    cached = cache_path(cache_dir, fingerprint)
    cached.write_text(json.dumps({
        "format_version": cached_version,
        "fingerprint": fingerprint,
        "profile": {"entities": [{"name": "measurements", "row_count": 2, "fields": [{
            "name": "quantity", "data_type": "string", "semantic_type": "phone",
            "sensitive": True,
        }]}]},
    }))

    assert load_cached_profile(source, cache_dir=cache_dir) is None
    profile = profile_example_folder(source, cache_dir=cache_dir)
    field = profile.entity("measurements").field("quantity")
    assert field.data_type == "integer"
    assert field.semantic_type is None
    assert field.sensitive
    assert json.loads(cached.read_text())["format_version"] == PROFILE_CACHE_FORMAT_VERSION
    assert load_cached_profile(source, cache_dir=cache_dir) == profile
