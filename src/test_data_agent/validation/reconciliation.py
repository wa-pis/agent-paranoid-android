"""Combined validation report."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from pydantic import BaseModel, Field, model_serializer

from test_data_agent.core.dataset import DatasetSpec
from test_data_agent.core.limits import GenerationBudget
from test_data_agent.core.settings import GenerationMode, ValidationSettings
from test_data_agent.rules.validation import BusinessValidationReport, validate_business_rules
from test_data_agent.rules.contract import validate_business_rules_for_spec
from test_data_agent.safety import SpecSafetyError, assert_spec_safe, validate_generated_row_privacy
from test_data_agent.validation.constraint_validator import validate_constraints
from test_data_agent.validation.relationship_validator import RelationshipMetrics, validate_relationships
from test_data_agent.validation.schema_validator import validate_schema


class ValidationSection(BaseModel):
    name: str
    passed: int = 0
    failed: int = 0
    errors: list[str] = Field(default_factory=list)
    checked: int | None = Field(default=None)
    relationship_metrics: list[RelationshipMetrics] | None = Field(default=None)

    @model_serializer(mode="wrap")
    def serialize_optional_fields(self, handler: Any) -> dict[str, Any]:
        payload: dict[str, Any] = handler(self)
        for name in ("checked", "relationship_metrics"):
            if getattr(self, name) is None:
                payload.pop(name, None)
        return payload


class DatasetValidationReport(BaseModel):
    valid: bool
    sections: list[ValidationSection]
    settings: ValidationSettings = Field(default_factory=ValidationSettings)
    business_validation: BusinessValidationReport | None = Field(default=None)

    @model_serializer(mode="wrap")
    def serialize_optional_fields(self, handler: Any) -> dict[str, Any]:
        payload: dict[str, Any] = handler(self)
        for name in ("business_validation",):
            if getattr(self, name) is None:
                payload.pop(name, None)
        return payload


def validate_dataset(
    rows_by_entity: dict[str, list[dict[str, Any]]],
    spec: DatasetSpec,
    *,
    budget: GenerationBudget | None = None,
) -> DatasetValidationReport:
    budget = budget or GenerationBudget()
    settings = spec.validation_settings.model_copy(deep=True)
    metrics: list[RelationshipMetrics] = []
    validators: list[tuple[str, bool, Callable[[], list[str]]]] = [
        ("schema", settings.validate_schema, lambda: validate_schema(rows_by_entity, spec)),
        (
            "relationships",
            settings.validate_relationships,
            lambda: validate_relationships(rows_by_entity, spec, budget=budget, metrics=metrics),
        ),
        (
            "constraints",
            settings.validate_constraints,
            lambda: validate_constraints(rows_by_entity, spec, budget=budget),
        ),
        ("privacy", settings.validate_privacy, lambda: validate_privacy(spec) or validate_generated_row_privacy(rows_by_entity, spec, parse_numeric_strings=True)),
    ]
    sections: list[ValidationSection] = []
    for name, enabled, validator in validators:
        if not enabled:
            continue
        result = section(name, validator())
        if name == "relationships":
            result.checked = len(metrics)
            result.passed = sum(item.valid for item in metrics)
            result.relationship_metrics = metrics
        sections.append(result)
        if settings.fail_fast and result.failed:
            break
    business = None
    if spec.business_rules is not None:
        validate_business_rules_for_spec(spec.business_rules, spec)
        business = validate_business_rules(rows_by_entity, spec.business_rules, budget=budget, spec=spec)
        sections.append(ValidationSection(name="business_rules", passed=business.rule_pass_count,
                                          failed=business.rule_fail_count, checked=business.rule_count,
                                          errors=[error for result in business.results for error in result.errors]))
    return DatasetValidationReport(
        business_validation=business,
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
    rows_by_entity: dict[str, list[dict[str, Any]]],
    spec: DatasetSpec,
    *,
    budget: GenerationBudget | None = None,
) -> None:
    """Enforce invariants independently of optional validation report settings."""
    budget = budget or GenerationBudget()
    budget.check("post-solve validation")
    assert_spec_safe(spec)
    if validate_generated_row_privacy(rows_by_entity, spec):
        raise GenerationValidationError("generated dataset failed post-solve privacy validation")
    if spec.generation_settings.mode in {GenerationMode.MIXED, GenerationMode.NEGATIVE}:
        return
    if validate_schema(rows_by_entity, spec):
        raise GenerationValidationError("generated dataset failed post-solve type validation")
    if spec.business_rules is not None:
        validate_business_rules_for_spec(spec.business_rules, spec)
        if not validate_business_rules(rows_by_entity, spec.business_rules, budget=budget, spec=spec).valid:
            raise GenerationValidationError("generated dataset failed post-solve business-rule validation")
    if validate_relationships(rows_by_entity, spec, budget=budget) or validate_constraints(rows_by_entity, spec, budget=budget):
        raise GenerationValidationError("generated dataset failed post-solve constraint validation")
