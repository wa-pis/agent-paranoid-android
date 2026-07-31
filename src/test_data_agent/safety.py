"""Safety checks shared by local and MCP generation workflows."""

from __future__ import annotations

import csv
import json
import re
from collections.abc import Iterable, Mapping
from pathlib import Path
from typing import Any

from test_data_agent.core.dataset import DatasetProfile, DatasetSpec
from test_data_agent.core.limits import (
    configure_csv_field_limit,
    enforce_input_cell_count,
    enforce_input_column_count,
    enforce_input_files,
    enforce_input_row_count,
)
from test_data_agent.core.privacy import (
    PrivacyClassification,
    SENSITIVE_SEMANTIC_TYPES,
    infer_sensitive_type_from_values,
    is_sensitive_field,
)
from test_data_agent.csv_profiler import detect_csv_dialect, detect_csv_encoding, validate_csv_headers


class ProfileSafetyError(ValueError):
    """Raised when a profile contains raw-looking sensitive metadata."""


class SpecSafetyError(ValueError):
    """Raised when a generation spec could publish unsafe source-derived values."""


class SourceRowReuseError(ValueError):
    """Raised when generated output exactly repeats a source CSV row."""


_SAFE_SENSITIVE_DISTRIBUTIONS = frozenset({"masked_patterns", "synthetic_identifier"})
_TEXT_LENGTH_PATTERN = re.compile(r"text_len_\d+")


def assert_spec_safe(spec: DatasetSpec) -> None:
    """Reject unsafe distributions before generation or artifact publication."""

    if spec.privacy_settings.allow_raw_sensitive_values:
        raise SpecSafetyError("dataset spec cannot allow raw sensitive values")

    for entity in spec.entities:
        for field in entity.fields:
            sensitive = _spec_field_is_sensitive(spec, entity.name, field.name)
            if sensitive and not field.sensitive:
                raise SpecSafetyError(
                    f"dataset spec field {entity.name!r}.{field.name!r} must be marked sensitive"
                )
            if not field.distribution:
                continue

            kind = str(field.distribution.get("kind", ""))
            if sensitive and kind not in _SAFE_SENSITIVE_DISTRIBUTIONS:
                raise SpecSafetyError(
                    f"sensitive dataset spec field {entity.name!r}.{field.name!r} "
                    f"uses unsafe distribution kind {kind!r}"
                )
            if sensitive and kind == "masked_patterns":
                _validate_masked_patterns(
                    entity.name,
                    field.name,
                    field.distribution.get("patterns", []),
                    error_type=SpecSafetyError,
                    context="dataset spec",
                )
            if kind != "categorical":
                continue

            categories = field.distribution.get("categories", [])
            if len(categories) > spec.privacy_settings.max_safe_categories:
                raise SpecSafetyError(
                    f"dataset spec field {entity.name!r}.{field.name!r} exceeds the safe category limit"
                )
            detected = infer_sensitive_type_from_values(
                item.get("value") for item in categories if isinstance(item, dict)
            )
            if detected is not None:
                raise SpecSafetyError(
                    f"dataset spec field {entity.name!r}.{field.name!r} "
                    "contains raw-looking sensitive values"
                )


def _spec_field_is_sensitive(spec: DatasetSpec, entity_name: str, field_name: str) -> bool:
    field = spec.entity(entity_name).field(field_name)
    if field.sensitive or is_sensitive_field(field.name, field.semantic_type):
        return True
    sensitive_classes = {
        PrivacyClassification.SENSITIVE,
        PrivacyClassification.SECRET,
    }
    return any(
        rule.classification in sensitive_classes
        and (rule.entity is None or rule.entity == entity_name)
        and (rule.field is None or rule.field == field_name)
        for rule in spec.privacy_rules
    )


def assert_profile_safe(profile: DatasetProfile) -> None:
    """Reject raw distributions for fields that are or look sensitive."""

    for entity in profile.entities:
        for field in entity.fields:
            sensitive = field.sensitive or is_sensitive_field(field.name, field.semantic_type)
            if not field.distribution:
                continue
            kind = str(field.distribution.get("kind", ""))
            if kind == "categorical" and not sensitive:
                categories = field.distribution.get("categories", [])
                content_sensitive_type = infer_sensitive_type_from_values(
                    item.get("value") for item in categories if isinstance(item, dict)
                )
                if content_sensitive_type is not None:
                    raise ProfileSafetyError(
                        f"profile field {entity.name!r}.{field.name!r} contains raw-looking sensitive values"
                    )
            if not sensitive:
                continue
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
    enforce_input_files([source_path])
    configure_csv_field_limit(csv)
    encoding = detect_csv_encoding(source_path)
    with source_path.open(newline="", encoding=encoding) as handle:
        sample = handle.read(8192)
        handle.seek(0)
        reader = csv.DictReader(handle, dialect=detect_csv_dialect(sample))
        fieldnames = validate_csv_headers(reader.fieldnames)
        enforce_input_column_count(len(fieldnames), label="source CSV")
        reader.fieldnames = fieldnames
        signatures = {_row_signature(row, fieldnames) for row in generated}
        for row_count, source_row in enumerate(reader, start=1):
            enforce_input_row_count(row_count, label="source CSV")
            enforce_input_cell_count(row_count * len(fieldnames), label="source CSV")
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


def _validate_masked_patterns(
    entity_name: str,
    field_name: str,
    patterns: Any,
    *,
    error_type: type[ValueError] = ProfileSafetyError,
    context: str = "profile",
) -> None:
    if not isinstance(patterns, list):
        raise error_type(
            f"sensitive {context} field {entity_name!r}.{field_name!r} has invalid masked patterns"
        )
    for item in patterns:
        pattern = item.get("pattern") if isinstance(item, dict) else None
        if pattern in SENSITIVE_SEMANTIC_TYPES:
            continue
        if isinstance(pattern, str) and _TEXT_LENGTH_PATTERN.fullmatch(pattern):
            continue
        raise error_type(
            f"sensitive {context} field {entity_name!r}.{field_name!r} has a raw-looking masked pattern"
        )


def _row_signature(row: Mapping[str, Any], field_names: list[str]) -> str:
    values = ["" if row.get(name) is None else str(row.get(name)) for name in field_names]
    return json.dumps(values, ensure_ascii=True, separators=(",", ":"))
