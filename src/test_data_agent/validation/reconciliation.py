"""Combined validation report."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from pydantic import BaseModel, Field

from test_data_agent.core.dataset import DatasetSpec
from test_data_agent.core.settings import GenerationMode, ValidationSettings
from test_data_agent.safety import SpecSafetyError, assert_spec_safe, validate_generated_row_privacy
from test_data_agent.validation.constraint_validator import validate_constraints
from test_data_agent.validation.relationship_validator import validate_relationships
from test_data_agent.validation.schema_validator import validate_schema


class ValidationSection(BaseModel):
    name: str
    passed: int = 0
    failed: int = 0
    errors: list[str] = Field(default_factory=list)


class DatasetValidationReport(BaseModel):
    valid: bool
    sections: list[ValidationSection]
    settings: ValidationSettings = Field(default_factory=ValidationSettings)


def validate_dataset(rows_by_entity: dict[str, list[dict[str, Any]]], spec: DatasetSpec) -> DatasetValidationReport:
    settings = spec.validation_settings.model_copy(deep=True)
    validators: list[tuple[str, bool, Callable[[], list[str]]]] = [
        ("schema", settings.validate_schema, lambda: validate_schema(rows_by_entity, spec)),
        (
            "relationships",
            settings.validate_relationships,
            lambda: validate_relationships(rows_by_entity, spec),
        ),
        (
            "constraints",
            settings.validate_constraints,
            lambda: validate_constraints(rows_by_entity, spec),
        ),
        ("privacy", settings.validate_privacy, lambda: validate_privacy(spec) or validate_generated_row_privacy(rows_by_entity, spec, parse_numeric_strings=True)),
    ]
    sections: list[ValidationSection] = []
    for name, enabled, validator in validators:
        if not enabled:
            continue
        result = section(name, validator())
        sections.append(result)
        if settings.fail_fast and result.failed:
            break
    return DatasetValidationReport(
        valid=not any(item.failed for item in sections),
        sections=sections,
        settings=settings,
    )


def validate_privacy(spec: DatasetSpec) -> list[str]:
    try:
        assert_spec_safe(spec)
    except SpecSafetyError as exc:
        return [str(exc)]
    return []


def section(name: str, errors: list[str]) -> ValidationSection:
    return ValidationSection(name=name, passed=0 if errors else 1, failed=len(errors), errors=errors)


class GenerationValidationError(ValueError):
    """Raised when final rows cannot satisfy the requested generation contract."""


def assert_generated_dataset_valid(
    rows_by_entity: dict[str, list[dict[str, Any]]], spec: DatasetSpec,
) -> None:
    """Enforce invariants independently of optional validation report settings."""
    assert_spec_safe(spec)
    if validate_generated_row_privacy(rows_by_entity, spec):
        raise GenerationValidationError("generated dataset failed post-solve privacy validation")
    if spec.generation_settings.mode in {GenerationMode.MIXED, GenerationMode.NEGATIVE}:
        return
    if validate_schema(rows_by_entity, spec):
        raise GenerationValidationError("generated dataset failed post-solve type validation")
    if validate_relationships(rows_by_entity, spec) or validate_constraints(rows_by_entity, spec):
        raise GenerationValidationError("generated dataset failed post-solve constraint validation")
