"""Combined validation report."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any, Literal

from pydantic import BaseModel, Field, model_serializer

from test_data_agent.core.dataset import DatasetSpec
from test_data_agent.core.constraint import ConstraintType
from test_data_agent.core.fingerprints import model_fingerprint
from test_data_agent.core.limits import GenerationBudget
from test_data_agent.core.settings import GenerationMode, ValidationSettings
from test_data_agent.rules.validation import BusinessValidationReport, validate_business_rules
from test_data_agent.rules.contract import validate_business_rules_for_spec
from test_data_agent.safety import SpecSafetyError, assert_spec_safe, validate_generated_row_privacy
from test_data_agent.validation.constraint_validator import TemporalMetrics, validate_constraints
from test_data_agent.validation.relationship_validator import RelationshipMetrics, validate_relationships
from test_data_agent.validation.schema_validator import validate_schema
from test_data_agent.validation.relational_scenarios import RelationalScenarioEvidence, inspect_relational_scenarios


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


class ValidationUtilityEvidence(BaseModel):
    spec_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    evidence_scope: Literal["generated_dataset"] = "generated_dataset"
    active_relationships: int = Field(ge=0)
    relationship_checks: Literal["executed", "not_declared", "not_run"]
    active_temporal_constraints: int = Field(ge=0)
    temporal_checks: Literal["executed", "not_declared", "not_run"]
    temporal_metrics: list[TemporalMetrics] = Field(default_factory=list)
    unmodeled_relationship_count: None = None
    source_orphan_ratio: None = None
    source_fanout: None = None
    source_temporal_fidelity: Literal["unmeasured"] = "unmeasured"


class DatasetValidationReport(BaseModel):
    valid: bool
    sections: list[ValidationSection]
    settings: ValidationSettings = Field(default_factory=ValidationSettings)
    business_validation: BusinessValidationReport | None = Field(default=None)
    utility: ValidationUtilityEvidence | None = None
    relational_scenarios: RelationalScenarioEvidence | None = None

    @model_serializer(mode="wrap")
    def serialize_optional_fields(self, handler: Any) -> dict[str, Any]:
        payload: dict[str, Any] = handler(self)
        for name in ("business_validation", "utility", "relational_scenarios"):
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
    temporal_metrics: list[TemporalMetrics] = []
    mandatory = bool(spec.relational_scenarios)
    validators: list[tuple[str, bool, Callable[[], list[str]]]] = [
        ("schema", settings.validate_schema or mandatory, lambda: validate_schema(rows_by_entity, spec)),
        (
            "relationships",
            settings.validate_relationships or mandatory,
            lambda: validate_relationships(rows_by_entity, spec, budget=budget, metrics=metrics),
        ),
        (
            "constraints",
            settings.validate_constraints or mandatory,
            lambda: validate_constraints(rows_by_entity, spec, budget=budget, temporal_metrics=temporal_metrics),
        ),
        ("privacy", settings.validate_privacy or mandatory, lambda: validate_privacy(spec) or validate_generated_row_privacy(rows_by_entity, spec, parse_numeric_strings=True)),
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
    active_relationships = sum(
        item.status != "rejected" for item in budget.iter_rule_work(spec.relationships)
    )
    active_temporal = sum(
        item.status != "rejected" and item.type == ConstraintType.TEMPORAL
        for item in budget.iter_rule_work(spec.constraints)
    )
    executed = {item.name for item in sections}
    utility = ValidationUtilityEvidence(
        spec_sha256=model_fingerprint(spec),
        active_relationships=active_relationships,
        relationship_checks=("not_declared" if not active_relationships else
                             "executed" if "relationships" in executed else "not_run"),
        active_temporal_constraints=active_temporal,
        temporal_checks=("not_declared" if not active_temporal else
                         "executed" if "constraints" in executed else "not_run"),
        temporal_metrics=temporal_metrics,
    )
    scenario_evidence = (inspect_relational_scenarios(rows_by_entity, spec, tuple(spec.relational_scenarios), budget=budget)
                         if spec.relational_scenarios else None)
    budget.check("validation evidence")
    return DatasetValidationReport(
        relational_scenarios=scenario_evidence,
        utility=utility,
        business_validation=business,
        valid=not any(item.failed for item in sections) and (scenario_evidence is None or
            scenario_evidence.expectations_met and all(item.valid for item in scenario_evidence.observations)),
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
    if spec.relational_scenarios:
        evidence = inspect_relational_scenarios(rows_by_entity, spec, tuple(spec.relational_scenarios), budget=budget)
        if not evidence.expectations_met:
            raise GenerationValidationError("generated dataset failed relational scenario reconciliation")
    elif spec.generation_settings.mode in {GenerationMode.MIXED, GenerationMode.NEGATIVE}:
        return
    if validate_schema(rows_by_entity, spec):
        raise GenerationValidationError("generated dataset failed post-solve type validation")
    if spec.business_rules is not None:
        validate_business_rules_for_spec(spec.business_rules, spec)
        if not validate_business_rules(rows_by_entity, spec.business_rules, budget=budget, spec=spec).valid:
            raise GenerationValidationError("generated dataset failed post-solve business-rule validation")
    if (not spec.relational_scenarios and validate_relationships(rows_by_entity, spec, budget=budget)) or validate_constraints(rows_by_entity, spec, budget=budget):
        raise GenerationValidationError("generated dataset failed post-solve constraint validation")
