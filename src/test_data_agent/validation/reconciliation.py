"""Combined validation report."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from test_data_agent.core.dataset import DatasetSpec
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


def validate_dataset(rows_by_entity: dict[str, list[dict[str, Any]]], spec: DatasetSpec) -> DatasetValidationReport:
    schema_errors = validate_schema(rows_by_entity, spec)
    relationship_errors = validate_relationships(rows_by_entity, spec)
    constraint_errors = validate_constraints(rows_by_entity, spec)
    sections = [
        section("schema", schema_errors),
        section("relationships", relationship_errors),
        section("constraints", constraint_errors),
    ]
    return DatasetValidationReport(valid=not any(item.failed for item in sections), sections=sections)


def section(name: str, errors: list[str]) -> ValidationSection:
    return ValidationSection(name=name, passed=0 if errors else 1, failed=len(errors), errors=errors)
