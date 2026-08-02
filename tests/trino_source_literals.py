from __future__ import annotations

import base64
import json
from collections.abc import Iterator, Mapping
from datetime import UTC, date, datetime
from decimal import Decimal
from uuid import UUID


SOURCE_LITERAL_VALUES: dict[str, object] = {
    "string": "source-string::rc4-private-value",
    "integer": 900_000_007,
    "decimal": Decimal("900000007.125001"),
    "float": 900_000_007.25,
    "boolean": False,
    "date": date(2087, 4, 5),
    "timestamp_tz": datetime(2087, 4, 5, 6, 7, 8, tzinfo=UTC),
    "uuid": UUID("f47ac10b-58cc-4372-a567-0e02b2c3d479"),
    "binary": b"\x00source-binary::rc4-private-value\xff",
    "base64_like": "c291cmNlLWJhc2U2NDo6cmM0LXByaXZhdGUtdmFsdWU=",
    "unicode": "source-unicode::Приватное-源-値",
    "nested_json": {
        "private": {
            "label": "source-nested::rc4-private-value",
            "values": [900_000_031, False, None],
        }
    },
}

SOURCE_ROWS: tuple[dict[str, object], ...] = (
    {**SOURCE_LITERAL_VALUES, "nullable_metric": None},
    {"nullable_metric": "source-null-companion::rc4-private-value"},
)


def literal_fingerprint(value: object) -> str:
    if value is None:
        return "null:null"
    if type(value) is bool:
        return f"boolean:{json.dumps(value)}"
    if type(value) is int:
        return f"integer:{value}"
    if type(value) is float:
        return f"float:{value!r}"
    if isinstance(value, str):
        return f"string:{json.dumps(value, ensure_ascii=True)}"
    raise TypeError(f"unsupported serialized literal type: {type(value).__name__}")


def serialized_source_fingerprints() -> frozenset[str]:
    serialized_rows = _json_safe(SOURCE_ROWS)
    return frozenset(
        literal_fingerprint(value) for value in _iter_leaf_values(serialized_rows)
    )


def assert_source_literals_absent(value: object) -> None:
    observed = {
        literal_fingerprint(item) for item in _iter_leaf_values(value)
    }
    leaked = serialized_source_fingerprints() & observed
    assert not leaked, f"source literal fingerprints leaked: {sorted(leaked)}"


def _json_safe(value: object) -> object:
    if isinstance(value, Mapping):
        return {name: _json_safe(item) for name, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(item) for item in value]
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, UUID):
        return str(value)
    if isinstance(value, bytes):
        return base64.b64encode(value).decode("ascii")
    return value


def _iter_leaf_values(value: object) -> Iterator[object]:
    if isinstance(value, Mapping):
        for item in value.values():
            yield from _iter_leaf_values(item)
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            yield from _iter_leaf_values(item)
        return
    yield value
