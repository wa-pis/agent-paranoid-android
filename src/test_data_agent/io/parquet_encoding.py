"""Portable scalar representations for explicitly malformed or wide Arrow cells."""

from __future__ import annotations

import json
from datetime import date, datetime
from decimal import Decimal
from typing import Any

from test_data_agent.core.decimal_units import decimal_to_text
from test_data_agent.core.serialization import load_limited_json

SCALAR_ENCODING_KEY = b"apa.scalar_encoding"


def encode_scalar(value: Any) -> str:
    if isinstance(value, Decimal):
        value = decimal_to_text(value)
    elif isinstance(value, date | datetime):
        value = value.isoformat()
    if value is not None and type(value) not in {str, int, float, bool}:
        raise ValueError("unsupported Parquet logical scalar")
    return json.dumps(value, ensure_ascii=True, allow_nan=False)


def decode_batch_rows(batch: Any) -> list[dict[str, Any]]:
    encodings = {
        field.name: (field.metadata or {}).get(SCALAR_ENCODING_KEY)
        for field in batch.schema
    }
    if any(
        value not in {None, b"json-v1", b"integer-text-v1"}
        for value in encodings.values()
    ):
        raise ValueError("unsupported Parquet scalar encoding")
    rows: list[dict[str, Any]] = batch.to_pylist()
    for row in rows:
        for name, encoding in encodings.items():
            value = row[name]
            if encoding is None or value is None:
                continue
            if not isinstance(value, str):
                raise ValueError("invalid Parquet scalar encoding")
            if encoding == b"integer-text-v1":
                try:
                    row[name] = int(value)
                except ValueError:
                    raise ValueError("invalid Parquet integer encoding") from None
            else:
                decoded = load_limited_json(value, label="Parquet logical scalar")
                if decoded is not None and type(decoded) not in {str, int, float, bool}:
                    raise ValueError("invalid Parquet scalar encoding")
                row[name] = decoded
    return rows
