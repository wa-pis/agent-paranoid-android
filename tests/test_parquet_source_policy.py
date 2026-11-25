"""Native schema typing preserves the released bounded Parquet inspection."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pyarrow as pa
import pyarrow.parquet as pq
import pytest

from test_data_agent.adapters.parquet_dataset import (
    _csv_data_type_from_arrow,
    dataset_profile_from_parquet,
    dataset_spec_from_parquet,
    parquet_file_to_dataset_profile,
)
from test_data_agent.generation import generate_dataset


@pytest.mark.parametrize(("arrow_type", "expected"), [
    (pa.int64(), "integer"),
    (pa.uint32(), "integer"),
    (pa.float64(), "float"),
    (pa.decimal128(12, 2), "decimal"),
    (pa.bool_(), "boolean"),
    (pa.date32(), "date"),
    (pa.timestamp("us", tz="UTC"), "datetime"),
    (pa.dictionary(pa.int8(), pa.string()), "string"),
    (pa.dictionary(pa.int8(), pa.int32()), "integer"),
    (pa.list_(pa.int64()), "string"),
    (pa.struct([("measure", pa.int64())]), "string"),
    (pa.map_(pa.string(), pa.int64()), "string"),
])
def test_arrow_scalar_meaning_does_not_match_nested_type_spelling(
    arrow_type: Any, expected: str,
) -> None:
    assert _csv_data_type_from_arrow(arrow_type) == expected


@pytest.mark.parametrize("entrypoint", [parquet_file_to_dataset_profile, dataset_profile_from_parquet])
def test_native_schema_types_retain_released_content_and_distinct_scan(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, entrypoint: Any,
) -> None:
    path = tmp_path / "records.parquet"
    pq.write_table(pa.table({
        "measure": pa.array([1, 2, 2], type=pa.int64()),
        "items": pa.array([[1], [2], None], type=pa.list_(pa.int64())),
        "phone_count": pa.array([1, 2, 3], type=pa.int64()),
        "access_token": pa.array([None, None, None], type=pa.string()),
    }), path)
    calls = []
    original = pq.ParquetFile.iter_batches

    def inspect(self: Any, *args: Any, **kwargs: Any) -> Any:
        calls.append(kwargs.get("batch_size"))
        return original(self, *args, **kwargs)

    monkeypatch.setattr(pq.ParquetFile, "iter_batches", inspect)
    result = entrypoint(path).entity("records")

    assert calls == [256]
    assert result.field("measure").data_type == "integer"
    assert result.field("measure").unique_ratio == 2 / 3
    assert result.field("measure").unique_ratio_kind == "exact"
    assert result.field("items").data_type == "string"
    assert result.field("items").sensitive
    assert result.field("items").unique_ratio is None
    assert result.field("phone_count").data_type == "integer"
    assert result.field("phone_count").sensitive
    assert result.field("access_token").sensitive
    assert all(field.semantic_type is None for field in result.fields)


def test_parquet_spec_seed_override_stays_deterministic(tmp_path: Path) -> None:
    path = tmp_path / "records.parquet"
    pq.write_table(pa.table({"measure": pa.array([1, 2], type=pa.int64())}), path)

    first = dataset_spec_from_parquet(path, count=3, seed=17)
    second = dataset_spec_from_parquet(path, count=3, seed=17)

    assert first == second
    assert first.generation_settings.seed == 17
    assert first.entity("records").row_count == 3
    generated = generate_dataset(first, seed=first.generation_settings.seed)
    assert generated == generate_dataset(second, seed=second.generation_settings.seed)
    assert all(type(row["measure"]) is int for row in generated["records"])
