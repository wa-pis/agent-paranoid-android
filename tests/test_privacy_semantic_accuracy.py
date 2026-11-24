"""Independent synthetic labels measure semantic accuracy and privacy separately.

The corpus is deliberately adversarial, not a prevalence estimate for real data.
Failures report case identifiers and classifications, never candidate spellings.
"""

from __future__ import annotations

import csv
import json
import random
from collections import Counter
from collections.abc import Callable, Iterator
from pathlib import Path
from typing import Any

import pytest

from test_data_agent.adapters import csv_profile_to_dataset_spec
from test_data_agent.core.dataset import DatasetSpec
from test_data_agent.core.field import FieldProfile
from test_data_agent.core.privacy import validate_local_category_values
from test_data_agent.csv_profiler import (
    CSVColumnAccumulator,
    CSVColumnProfile,
    profile_column,
    profile_csv,
)
from test_data_agent.generation import generate_dataset, infer_dataset_spec
from test_data_agent.profiling import profile_example_folder
from test_data_agent.profiling.schema_profiler import FieldAccumulator, profile_field
from test_data_agent.safety import validate_generated_row_privacy
from test_data_agent.validation import validate_dataset


_CORPUS_PATH = Path(__file__).parent / "fixtures" / "privacy_semantic_accuracy.json"
_CASES: list[dict[str, Any]] = json.loads(_CORPUS_PATH.read_text())["cases"]


def _values(case: dict[str, Any]) -> list[str]:
    return [
        "".join(group["parts"])
        for group in case["groups"]
        for _ in range(group["count"])
    ]


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


def accuracy_report(
    classify: Callable[[str, list[str], int], CSVColumnProfile] = profile_column,
) -> dict[str, dict[str, int | float | None]]:
    """Aggregate only hand-labeled outcomes; supports a frozen baseline callable."""
    groups: dict[str, Counter[str]] = {}
    for case in _CASES:
        values = _values(case)
        profile = classify(case["field"], values, len(values))
        counts = groups.setdefault(case["family"], Counter())
        expected, actual = case["semantic"], profile.semantic_type
        counts["cases"] += 1
        counts["tp"] += int(expected is not None and actual == expected)
        counts["fp"] += int(actual is not None and actual != expected)
        counts["fn"] += int(expected is not None and actual != expected)
        counts["tn"] += int(expected is None and actual is None)
        counts["privacy_fp"] += int(profile.sensitive and not case["sensitive"])
        counts["privacy_fn"] += int(case["sensitive"] and not profile.sensitive)
    report: dict[str, dict[str, int | float | None]] = {}
    for family, counts in sorted(groups.items()):
        report[family] = dict(counts)
        precision_denominator = counts["tp"] + counts["fp"]
        recall_denominator = counts["tp"] + counts["fn"]
        report[family]["precision"] = (
            counts["tp"] / precision_denominator if precision_denominator else None
        )
        report[family]["recall"] = (
            counts["tp"] / recall_denominator if recall_denominator else None
        )
    return report


@pytest.mark.parametrize("case", _CASES, ids=[case["id"] for case in _CASES])
def test_labeled_semantics_and_risk_are_independent_and_order_invariant(case: dict[str, Any]) -> None:
    values = _values(case)
    outcomes = []
    for ordered in _orders(values):
        observed = []
        for profile in _views(case["field"], ordered):
            observed.append((profile.data_type, profile.semantic_type, profile.sensitive))
            assert profile.semantic_type == case["semantic"], (
                f"semantic mismatch for synthetic case {case['id']}"
            )
            assert profile.sensitive is case["sensitive"], (
                f"risk mismatch for synthetic case {case['id']}"
            )
            if case["sensitive"]:
                serialized = profile.model_dump_json()
                protected = {value for value in values if len(value) >= 7}
                assert all(value not in serialized for value in protected), (
                    f"input spelling exposed for synthetic case {case['id']}"
                )
                if isinstance(profile, CSVColumnProfile):
                    assert profile.top_values == []
                    assert all(getattr(profile, key) is None for key in (
                        "min_value", "max_value", "p05", "p95", "min_date", "max_date",
                        "min_timestamp", "max_timestamp",
                    ))
                else:
                    assert not {"min_value", "max_value", "p05", "p95"}.intersection(
                        profile.distribution,
                    )
        outcomes.append(observed)
    assert outcomes[0] == outcomes[1] == outcomes[2], (
        f"permutation mismatch for synthetic case {case['id']}"
    )


def test_semantic_accuracy_corpus_has_positive_and_negative_labels_per_target_family() -> None:
    assert len({case["id"] for case in _CASES}) == len(_CASES)
    for family in ("ssn", "card", "entropy", "strong"):
        candidates = [case for case in _CASES if case["family"] == family]
        assert any(case["semantic"] is not None for case in candidates)
        assert any(case["semantic"] is None for case in candidates)
    for family, metrics in accuracy_report().items():
        assert metrics["fp"] == 0, f"semantic false positives in synthetic family {family}"
        assert metrics["fn"] == 0, f"semantic false negatives in synthetic family {family}"
        assert metrics["privacy_fp"] == 0, f"risk false positives in synthetic family {family}"
        assert metrics["privacy_fn"] == 0, f"risk false negatives in synthetic family {family}"


@pytest.mark.parametrize("case_id", ["ssn_bare_quantity", "card_neutral_sku", "entropy_product_hash"])
def test_weak_semantics_do_not_authorize_raw_rows_or_local_categories(case_id: str) -> None:
    case = next(case for case in _CASES if case["id"] == case_id)
    value = _values(case)[0]
    profile = profile_column("payload", [value], 1)
    assert profile.sensitive
    assert profile.semantic_type is None
    with pytest.raises(ValueError, match="sensitive"):
        validate_local_category_values(
            field_name="payload", semantic_type=profile.semantic_type,
            sensitive=profile.sensitive, values=[value],
        )
    spec = DatasetSpec.model_validate({
        "entities": [{"name": "records", "row_count": 1, "fields": [{
            "name": "payload", "data_type": "string", "sensitive": False,
        }]}],
    })
    failures = validate_generated_row_privacy({"records": [{"payload": value}]}, spec)
    assert failures == ["generated dataset failed post-solve privacy validation"]
    assert value not in " ".join(failures)


def test_public_weak_profiles_generate_synthetic_values_deterministically(tmp_path: Path) -> None:
    selected = [next(case for case in _CASES if case["id"] == case_id) for case_id in (
        "ssn_bare_quantity", "card_neutral_sku", "entropy_product_hash",
    )]
    path = tmp_path / "records.csv"
    source_rows = list(zip(*[_values(case) for case in selected], strict=True))
    with path.open("w", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["quantity", "stock_code", "digest"])
        writer.writerows(source_rows)
    single = profile_csv(path)
    folder = profile_example_folder(tmp_path, cache_dir=None)
    for profile in (single, folder):
        serialized = profile.model_dump_json()
        assert all(value not in serialized for row in source_rows for value in row)
    for spec in (
        csv_profile_to_dataset_spec(single, seed=42, count=8),
        infer_dataset_spec(folder, count=8),
    ):
        assert all(field.sensitive and field.semantic_type is None
                   for field in spec.entity("records").fields)
        rows = generate_dataset(spec, seed=42)
        assert rows == generate_dataset(spec, seed=42)
        assert validate_dataset(rows, spec).valid
        source_values = {value for row in source_rows for value in row}
        assert all(str(value) not in source_values for row in rows["records"] for value in row.values())
