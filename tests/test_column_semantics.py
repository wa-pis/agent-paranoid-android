"""Whole-column semantic inference uses evidence without exposing source text."""

import csv
import random
from collections.abc import Iterator
from pathlib import Path

import pytest

from test_data_agent import csv_profiler
from test_data_agent.adapters import csv_profile_to_dataset_spec
from test_data_agent.core.field import FieldProfile
from test_data_agent.core.privacy import SensitiveValueSignal
from test_data_agent.csv_profiler import (
    CSVColumnAccumulator,
    CSVColumnProfile,
    profile_column,
    profile_csv,
)
from test_data_agent.generation import generate_dataset, infer_dataset_spec
from test_data_agent.profiling import profile_example_folder
from test_data_agent.profiling import schema_profiler
from test_data_agent.profiling.schema_profiler import FieldAccumulator, profile_field
from test_data_agent.validation import validate_dataset


_EMAIL = "fictional" + "@" + "example.test"
_PHONE = "+1-202-" + "555-0100"
_SSN = "000-" + "00-" + "0000"
_SECRET = "sk" + "_test_" + "A1b2C3d4E5f6"
_ORDINARY = "ordinary_category"


def _views(name: str, values: list[str]) -> Iterator[CSVColumnProfile | FieldProfile]:
    yield profile_column(name, values, len(values))
    yield profile_field(name, values, len(values))
    single = CSVColumnAccumulator(name)
    folder = FieldAccumulator(name)
    for value in values:
        single.add(value)
        folder.add(value)
    yield single.to_profile(len(values))
    yield folder.to_profile(len(values))


def _orders(values: list[str]) -> Iterator[list[str]]:
    yield values
    yield list(reversed(values))
    shuffled = list(values)
    random.Random(20261122).shuffle(shuffled)
    yield shuffled


def _assert_sensitive_without_source_values(
    profile: CSVColumnProfile | FieldProfile, values: tuple[str, ...],
) -> None:
    assert profile.sensitive
    serialized = profile.model_dump_json()
    assert all(value not in serialized for value in values)
    if isinstance(profile, CSVColumnProfile):
        assert profile.top_values == []
        assert all(getattr(profile, name) is None for name in (
            "min_value", "max_value", "p05", "p95",
        ))


@pytest.mark.parametrize("name", [
    "email_count", "phone_count", "voicemail_count", "headphone_count",
    "emailCount", "phoneCount", "phone-count", "EMAIL_COUNT",
], ids=["email_count", "phone_count", "voicemail_count", "headphone_count",
        "camel_email_count", "camel_phone_count", "hyphen_count", "upper_count"])
def test_measure_name_tokens_do_not_change_numeric_fields_into_contacts(name: str) -> None:
    for profile in _views(name, ["2", "3"]):
        assert profile.data_type == "integer"
        assert profile.semantic_type is None
        # Name-based safety remains conservative despite the semantic correction.
        assert profile.sensitive


@pytest.mark.parametrize("name", ["filename", "cardinality", "headphone", "voicemail"])
def test_substring_names_do_not_assign_contact_semantics(name: str) -> None:
    for profile in _views(name, [_ORDINARY, "another_category"]):
        assert profile.data_type == "string"
        assert profile.semantic_type is None


def test_sparse_conflicting_matches_do_not_define_a_column_and_ignore_row_order() -> None:
    values = [_EMAIL, _PHONE] + [_ORDINARY] * 98
    outcomes = []
    for ordered in _orders(values):
        profiles = list(_views("payload", ordered))
        outcomes.append([(p.data_type, p.semantic_type, p.sensitive) for p in profiles])
        for profile in profiles:
            assert profile.semantic_type is None
            assert profile.data_type == "string"
            _assert_sensitive_without_source_values(profile, (_EMAIL, _PHONE))
    assert outcomes[0] == outcomes[1] == outcomes[2]


@pytest.mark.parametrize("value,kind", [(_EMAIL, "email"), (_PHONE, "phone"), (_SSN, "ssn")],
                         ids=["email", "phone", "ssn"])
@pytest.mark.parametrize("matches", [79, 80], ids=["below_threshold", "inclusive_threshold"])
def test_dominance_threshold_counts_all_nonempty_values(
    value: str, kind: str, matches: int,
) -> None:
    values = [value] * matches + [_ORDINARY] * (100 - matches) + ["", " \t"]
    for ordered in _orders(values):
        for profile in _views("payload", ordered):
            assert profile.semantic_type == (kind if matches == 80 else None)
            _assert_sensitive_without_source_values(profile, (value,))


@pytest.mark.parametrize("prefix_email", [True, False], ids=["minority_first", "minority_last"])
def test_first_hundred_values_cannot_override_whole_column_dominance(prefix_email: bool) -> None:
    minority = [_EMAIL] * 100
    majority = [_ORDINARY] * 400
    values = minority + majority if prefix_email else majority + minority
    for profile in _views("payload", values):
        assert profile.semantic_type is None
        assert profile.data_type == "string"
        _assert_sensitive_without_source_values(profile, (_EMAIL,))


def test_conflicting_equal_matches_abstain_independently_of_order() -> None:
    for ordered in _orders([_EMAIL] * 50 + [_PHONE] * 50):
        for profile in _views("payload", ordered):
            assert profile.semantic_type is None
            _assert_sensitive_without_source_values(profile, (_EMAIL, _PHONE))


@pytest.mark.parametrize("name", ["payload", "customerPhone"], ids=["neutral_name", "phone_hint"])
@pytest.mark.parametrize("other", [_ORDINARY, _EMAIL], ids=["ordinary_majority", "email_majority"])
def test_single_secret_retains_protection_outside_dominant_semantics(name: str, other: str) -> None:
    values = [other] * 101 + [_SECRET]
    for ordered in _orders(values):
        for profile in _views(name, ordered):
            assert profile.semantic_type == "secret"
            _assert_sensitive_without_source_values(profile, (_SECRET, _EMAIL))


@pytest.mark.parametrize("name,value", [("customer_email", _PHONE), ("customerPhone", _EMAIL)],
                         ids=["email_name_phone_content", "phone_name_email_content"])
def test_name_hint_conflicting_with_dominant_content_abstains(name: str, value: str) -> None:
    for ordered in _orders([value] * 80 + [_ORDINARY] * 20):
        for profile in _views(name, ordered):
            assert profile.semantic_type is None
            assert profile.data_type == "string"
            _assert_sensitive_without_source_values(profile, (value,))


@pytest.mark.parametrize("name,values,semantic_type", [
    ("quantity", ["12025550100", "12025550101"], None),
    ("phone_count", ["12025550100", "12025550101"], None),
    ("customerPhone", ["12025550100", "12025550101"], "phone"),
    ("CustomerPHONE", ["12025550100", "12025550101"], "phone"),
    ("phone", ["2", "3"], None),
    ("customerPhone", ["2", "3"], None),
], ids=["neutral_numeric", "numeric_role", "camel_phone", "acronym_phone",
        "unrecognized_phone", "unrecognized_camel_phone"])
def test_numeric_phone_semantics_require_both_recognition_and_name_context(
    name: str, values: list[str], semantic_type: str | None,
) -> None:
    for profile in _views(name, values):
        assert profile.semantic_type == semantic_type
        assert profile.data_type in ({"phone", "string"} if semantic_type else {"integer"})


@pytest.mark.parametrize("value,kind", [(_EMAIL, "email"), (_PHONE, "phone")],
                         ids=["email_content", "phone_content"])
def test_ambiguous_name_tokens_leave_dominant_content_to_decide(value: str, kind: str) -> None:
    for profile in _views("emailAddress", [value]):
        assert profile.semantic_type == kind
        _assert_sensitive_without_source_values(profile, (value,))


@pytest.mark.parametrize("name,kind", [("full_name", "name"), ("billingAddress", "address")],
                         ids=["name_hint", "address_hint"])
def test_name_and_address_hints_remain_for_nonnumeric_unrecognized_content(
    name: str, kind: str,
) -> None:
    for profile in _views(name, [_ORDINARY, "another_category"]):
        assert profile.semantic_type == kind
        assert profile.sensitive


@pytest.mark.parametrize("name", ["payload", "customerPhone", "full_name", "email_address"])
def test_all_null_column_does_not_assign_semantics_from_name(name: str) -> None:
    for profile in _views(name, ["", " \t"]):
        assert profile.semantic_type is None
        assert profile.nullable


@pytest.mark.parametrize("name,values,kind", [
    ("full_name", ["2026-01-01", "2026-01-02"], "name"),
    ("address", ["true", "false"], "address"),
    ("billingAddress", ["2026-01-01T12:00:00", "2026-01-02T12:00:00"], "address"),
    ("ssn", ["000000000", "000000001"], "ssn"),
], ids=["date_name", "boolean_address", "timestamp_address", "compact_ssn"])
def test_resolved_text_semantics_preserve_text_physical_types_across_views(
    name: str, values: list[str], kind: str,
) -> None:
    for ordered in _orders(values):
        for profile in _views(name, ordered):
            assert profile.semantic_type == kind
            expected = kind if isinstance(profile, CSVColumnProfile) and kind in {"name", "address"} else "string"
            assert profile.data_type == expected
            assert profile.sensitive


def test_column_evidence_retains_fixed_aggregate_counters_without_source_text() -> None:
    marker = "fictional raw marker"
    evidence = csv_profiler._column_semantic_evidence(f"{marker} {i}" for i in range(300))
    signals = tuple(SensitiveValueSignal)
    for _ in range(1000):
        for signal in signals:
            evidence.add(signal, numeric=False)
    assert evidence.non_null_count == 300 + 1000 * len(signals)
    assert set(evidence.matches) == set(signals)
    assert sum(evidence.matches.values()) == 1000 * len(signals)
    assert marker not in repr(evidence)
    assert all(isinstance(signal, SensitiveValueSignal) for signal in evidence.matches)


@pytest.mark.parametrize("view", ["single", "folder"])
def test_accumulator_classifies_once_and_resolver_reuses_evidence(
    monkeypatch: pytest.MonkeyPatch, view: str,
) -> None:
    module = csv_profiler if view == "single" else schema_profiler
    accumulator = CSVColumnAccumulator("payload") if view == "single" else FieldAccumulator("payload")
    original = module._csv_sensitive_signal
    calls: list[None] = []

    def classify(value: str, *, max_chars: int | None = None) -> SensitiveValueSignal | None:
        calls.append(None)
        return original(value, max_chars=max_chars)

    monkeypatch.setattr(module, "_csv_sensitive_signal", classify)
    for value in (_EMAIL, _PHONE, _ORDINARY, "", " \t", None):
        accumulator.add(value)
    assert len(calls) == 3
    for name in ("payload", "customerPhone", "email_count"):
        accumulator.semantic_evidence.resolve(name)
    assert len(calls) == 3


def test_public_profiles_keep_counter_roles_and_generate_deterministically(tmp_path: Path) -> None:
    path = tmp_path / "events.csv"
    with path.open("w", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["email_count", "phone_count"])
        writer.writerows([[2, 3], [4, 5]])

    single = profile_csv(path)
    folder = profile_example_folder(tmp_path, cache_dir=None)
    specs = (
        csv_profile_to_dataset_spec(single, seed=42, count=8),
        infer_dataset_spec(folder, count=8),
    )
    for spec in specs:
        fields = spec.entity("events").fields
        assert all(field.data_type == "integer" and field.semantic_type is None for field in fields)
        rows = generate_dataset(spec, seed=42)
        assert rows == generate_dataset(spec, seed=42)
        assert all(type(value) is int for row in rows["events"] for value in row.values())
        assert validate_dataset(rows, spec).valid


def test_public_sparse_sensitive_profiles_do_not_copy_rare_values(tmp_path: Path) -> None:
    path = tmp_path / "events.csv"
    values = [_EMAIL, _PHONE] + [_ORDINARY] * 98
    with path.open("w", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["payload"])
        writer.writerows([[value] for value in values])

    single = profile_csv(path)
    folder = profile_example_folder(tmp_path, cache_dir=None)
    for profile in (single.columns[0], folder.entity("events").field("payload")):
        assert profile.semantic_type is None
        _assert_sensitive_without_source_values(profile, (_EMAIL, _PHONE))
    for spec in (
        csv_profile_to_dataset_spec(single, seed=42, count=8),
        infer_dataset_spec(folder, count=8),
    ):
        assert spec.entity("events").field("payload").semantic_type is None
        rows = generate_dataset(spec, seed=42)
        assert rows == generate_dataset(spec, seed=42)
        assert validate_dataset(rows, spec).valid
        assert all(row["payload"] not in {_EMAIL, _PHONE} for row in rows["events"])
