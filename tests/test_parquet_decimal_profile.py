"""Declared Parquet decimals are schema evidence, not source-value bounds."""

from decimal import Decimal

import pytest

from test_data_agent.adapters.parquet_dataset import (
    parquet_file_to_dataset_profile,
    parquet_file_to_dataset_spec,
)
from test_data_agent.core.field import FieldType


def test_parquet_decimal_profile_preserves_declared_precision_without_values(tmp_path):
    pa = pytest.importorskip("pyarrow")
    pq = pytest.importorskip("pyarrow.parquet")
    path = tmp_path / "fictional.parquet"
    schema = pa.schema([
        pa.field("amount", pa.decimal128(20, 2)),
        pa.field("balance", pa.decimal128(38, 16)),
    ])
    pq.write_table(pa.Table.from_pylist([{
        "amount": Decimal("123.45"), "balance": Decimal("9007199254740993.1234567890123456"),
    }], schema=schema), path)

    profile = parquet_file_to_dataset_profile(path)
    amount, balance = profile.entities[0].fields
    assert profile.source_type == "parquet"
    assert (amount.data_type, amount.decimal_precision, amount.decimal_scale) == (
        FieldType.DECIMAL, 20, 2,
    )
    assert (balance.data_type, balance.decimal_precision, balance.decimal_scale) == (
        FieldType.DECIMAL, 38, 16,
    )
    assert amount.distribution == balance.distribution == {}
    assert "123.45" not in profile.model_dump_json()
    assert "9007199254740993" not in profile.model_dump_json()

    with pytest.raises(ValueError, match="decimal_range distribution"):
        parquet_file_to_dataset_spec(path)


def test_parquet_decimal_over_38_digits_fails_closed(tmp_path):
    pa = pytest.importorskip("pyarrow")
    pq = pytest.importorskip("pyarrow.parquet")
    path = tmp_path / "wide.parquet"
    pq.write_table(pa.Table.from_pylist([], schema=pa.schema([
        pa.field("amount", pa.decimal256(39, 2)),
    ])), path)
    with pytest.raises(ValueError, match="supported precision and scale"):
        parquet_file_to_dataset_profile(path)
