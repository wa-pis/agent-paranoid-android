from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from tests.trino_source_literals import (
    SOURCE_LITERAL_VALUES,
    SOURCE_ROWS,
    literal_fingerprint,
    serialized_source_fingerprints,
)


def test_source_literal_fixture_covers_supported_types() -> None:
    assert type(SOURCE_LITERAL_VALUES["string"]) is str
    assert type(SOURCE_LITERAL_VALUES["integer"]) is int
    assert isinstance(SOURCE_LITERAL_VALUES["decimal"], Decimal)
    assert type(SOURCE_LITERAL_VALUES["float"]) is float
    assert type(SOURCE_LITERAL_VALUES["boolean"]) is bool
    assert type(SOURCE_LITERAL_VALUES["date"]) is date
    assert isinstance(SOURCE_LITERAL_VALUES["timestamp_tz"], datetime)
    assert SOURCE_LITERAL_VALUES["timestamp_tz"].tzinfo is not None
    assert isinstance(SOURCE_LITERAL_VALUES["uuid"], UUID)
    assert isinstance(SOURCE_LITERAL_VALUES["binary"], bytes)
    assert type(SOURCE_LITERAL_VALUES["base64_like"]) is str
    unicode_value = SOURCE_LITERAL_VALUES["unicode"]
    assert isinstance(unicode_value, str)
    assert "源" in unicode_value
    assert isinstance(SOURCE_LITERAL_VALUES["nested_json"], dict)
    assert SOURCE_ROWS[0]["nullable_metric"] is None
    assert SOURCE_ROWS[1]["nullable_metric"] is not None


def test_source_literal_fingerprints_do_not_match_aggregate_counts() -> None:
    aggregate_count_fingerprints = {
        literal_fingerprint(count) for count in (0, 1, 2, 13, 77, 1000)
    }

    assert serialized_source_fingerprints().isdisjoint(
        aggregate_count_fingerprints
    )
    assert literal_fingerprint(False) != literal_fingerprint(0)
