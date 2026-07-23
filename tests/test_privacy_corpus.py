import json
from pathlib import Path

import pytest

from test_data_agent.core.privacy import (
    infer_sensitive_from_name,
    infer_sensitive_value_type,
)


CORPUS_PATH = Path(__file__).parent / "fixtures" / "privacy_detection_cases.json"


@pytest.fixture(scope="module")
def privacy_corpus() -> dict:
    return json.loads(CORPUS_PATH.read_text())


def test_privacy_value_corpus(privacy_corpus: dict) -> None:
    failures = []
    for case in privacy_corpus["value_cases"]:
        value = "".join(case["parts"])
        actual = infer_sensitive_value_type(value)
        if actual != case["expected"]:
            failures.append(
                {
                    "id": case["id"],
                    "expected": case["expected"],
                    "actual": actual,
                }
            )

    assert failures == []


def test_privacy_field_name_corpus(privacy_corpus: dict) -> None:
    failures = []
    for case in privacy_corpus["name_cases"]:
        actual = infer_sensitive_from_name(case["name"])
        if actual is not case["expected"]:
            failures.append(
                {
                    "name": case["name"],
                    "expected": case["expected"],
                    "actual": actual,
                }
            )

    assert failures == []
