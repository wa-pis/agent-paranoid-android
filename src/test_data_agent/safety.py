"""Safety checks shared by local and MCP generation workflows."""

from __future__ import annotations

import csv
import json
import re
from collections.abc import Iterable, Mapping
from pathlib import Path
from typing import Any

from test_data_agent.core.dataset import DatasetProfile
from test_data_agent.core.privacy import SENSITIVE_SEMANTIC_TYPES, is_sensitive_field
from test_data_agent.csv_profiler import detect_csv_dialect, detect_csv_encoding, validate_csv_headers


class ProfileSafetyError(ValueError):
    """Raised when a profile contains raw-looking sensitive metadata."""


class SourceRowReuseError(ValueError):
    """Raised when generated output exactly repeats a source CSV row."""


_SAFE_SENSITIVE_DISTRIBUTIONS = frozenset({"masked_patterns", "synthetic_identifier"})
_TEXT_LENGTH_PATTERN = re.compile(r"text_len_\d+")


def assert_profile_safe(profile: DatasetProfile) -> None:
    """Reject raw distributions for fields that are or look sensitive."""

    for entity in profile.entities:
        for field in entity.fields:
            sensitive = field.sensitive or is_sensitive_field(field.name, field.semantic_type)
            if not sensitive or not field.distribution:
                continue
            kind = str(field.distribution.get("kind", ""))
            if kind not in _SAFE_SENSITIVE_DISTRIBUTIONS:
                raise ProfileSafetyError(
                    f"sensitive profile field {entity.name!r}.{field.name!r} uses unsafe distribution kind {kind!r}"
                )
            if kind == "masked_patterns":
                _validate_masked_patterns(entity.name, field.name, field.distribution.get("patterns", []))


def assert_no_csv_source_rows(
    source_path: Path,
    generated_rows: Iterable[Mapping[str, Any]],
    *,
    entity_name: str | None = None,
) -> None:
    """Stream a CSV and fail without exposing values when any full row is reused."""

    generated = list(generated_rows)
    if not generated:
        return
    encoding = detect_csv_encoding(source_path)
    with source_path.open(newline="", encoding=encoding) as handle:
        sample = handle.read(8192)
        handle.seek(0)
        reader = csv.DictReader(handle, dialect=detect_csv_dialect(sample))
        fieldnames = validate_csv_headers(reader.fieldnames)
        reader.fieldnames = fieldnames
        signatures = {_row_signature(row, fieldnames) for row in generated}
        for source_row in reader:
            if _row_signature(source_row, fieldnames) in signatures:
                label = entity_name or source_path.stem
                raise SourceRowReuseError(
                    f"generated entity {label!r} repeats a complete source row; generation stopped"
                )


def assert_no_csv_folder_source_rows(
    source_folder: Path,
    generated_rows_by_entity: Mapping[str, Iterable[Mapping[str, Any]]],
) -> None:
    for entity_name, rows in generated_rows_by_entity.items():
        source_path = source_folder / f"{entity_name}.csv"
        if source_path.exists():
            assert_no_csv_source_rows(source_path, rows, entity_name=entity_name)


def _validate_masked_patterns(entity_name: str, field_name: str, patterns: Any) -> None:
    if not isinstance(patterns, list):
        raise ProfileSafetyError(
            f"sensitive profile field {entity_name!r}.{field_name!r} has invalid masked patterns"
        )
    for item in patterns:
        pattern = item.get("pattern") if isinstance(item, dict) else None
        if pattern in SENSITIVE_SEMANTIC_TYPES:
            continue
        if isinstance(pattern, str) and _TEXT_LENGTH_PATTERN.fullmatch(pattern):
            continue
        raise ProfileSafetyError(
            f"sensitive profile field {entity_name!r}.{field_name!r} has a raw-looking masked pattern"
        )


def _row_signature(row: Mapping[str, Any], field_names: list[str]) -> str:
    values = ["" if row.get(name) is None else str(row.get(name)) for name in field_names]
    return json.dumps(values, ensure_ascii=True, separators=(",", ":"))
