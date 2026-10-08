"""Provider-neutral, field-scoped local category projection and restoration."""

from __future__ import annotations

import ast
import copy
import json
import math
from collections.abc import Mapping
from typing import Any

from test_data_agent.advisor import AdvisorContractError, AdvisorProposal, AdvisorRequest
from test_data_agent.core.distribution import parse_date_bound, parse_datetime_bound
from test_data_agent.core.privacy import SENSITIVE_SEMANTIC_TYPES
from test_data_agent.rules.expressions import parse_safe_expression


class _ProviderRestorations(dict[tuple[str, str, str], Any]):
    """Local-only omitted metadata, restored only against its exact projection."""

    def __init__(self) -> None:
        super().__init__()
        self.original: dict[str, Any] = {}
        self.projected: dict[str, Any] = {}


_KNOWN_SEMANTIC_TYPES = frozenset(SENSITIVE_SEMANTIC_TYPES | {
    "identifier", "quasi_identifier", "quasi-identifier",
})


def _project_semantic_type(value: str | None) -> str | None:
    return value.lower() if value is not None and value.lower() in _KNOWN_SEMANTIC_TYPES else None


def _semantic_projection(dataset: dict[str, Any]) -> None:
    for key in ("source_type", "source_policy_version"):
        if key in dataset:
            dataset[key] = "provider_metadata" if key == "source_type" else None
    settings = dataset.get("generation_settings")
    if settings is not None:
        settings["locale"] = None
    for rule in dataset.get("privacy_rules", []):
        rule["reason"] = None
        rule["semantic_type"] = _project_semantic_type(rule.get("semantic_type"))
    for relationship in dataset.get("relationships", []):
        relationship["status"] = "inferred"
    for entity in dataset["entities"]:
        for field in entity["fields"]:
            field["semantic_type"] = _project_semantic_type(field.get("semantic_type"))
            distribution = field["distribution"]
            kind = distribution.get("kind")
            if kind == "synthetic_identifier":
                distribution["prefix"] = None
            elif kind == "masked_patterns":
                # Patterns are local generation configuration, not source-safe facts.
                distribution["patterns"] = []
            elif kind in {"date_range", "datetime_range"}:
                parser = parse_date_bound if kind == "date_range" else parse_datetime_bound
                for key in ("min", "max"):
                    value = distribution.get(key)
                    if value is not None:
                        parsed = parser(value, key)
                        assert parsed is not None
                        distribution[key] = parsed.isoformat()
    for constraint in dataset.get("constraints", []):
        kind = constraint["type"]
        constraint["expected"] = None  # Not used by dataset constraints.
        if kind != "formula":
            constraint["expression"] = None
        elif constraint.get("expression") is not None:
            try:
                tree = parse_safe_expression(constraint["expression"])
                known_fields = {field["name"] for entity in dataset["entities"]
                                if entity["name"] == constraint["entity"] for field in entity["fields"]}
                for node in ast.walk(tree):
                    if isinstance(node, ast.Constant) and type(node.value) not in (int, float):
                        # sum accepts a schema field name; other strings are data.
                        if not any(isinstance(parent, ast.Call) and isinstance(parent.func, ast.Name)
                                   and parent.func.id == "sum" and parent.args == [node]
                                   and node.value in known_fields
                                   for parent in ast.walk(tree)):
                            raise ValueError
                for node in ast.walk(tree):
                    if isinstance(node, ast.Name) and node.id not in known_fields | {"sum", "count"}:
                        raise ValueError
                constraint["expression"] = ast.unparse(tree)
            except (ValueError, TypeError, SyntaxError):
                raise AdvisorContractError("advisor formula metadata is invalid") from None
        condition = constraint.get("condition")
        if kind != "conditional_required":
            constraint["condition"] = None
        elif condition is not None:
            constraint["condition"] = {
                key: value for key, value in condition.items()
                if key in {"field", "equals", "not_equals", "in_values"}
            }
        if kind != "aggregate_mapping":
            for key in ("target_entity", "target_field", "aggregate"):
                constraint[key] = None


def _restore_semantic_metadata(payload: dict[str, Any], restorations: _ProviderRestorations) -> None:
    original, projected = restorations.original, restorations.projected
    for key in ("generation_settings", "privacy_rules", "relationships"):
        if original.get(key) != projected.get(key):
            if payload.get(key) != projected.get(key):
                raise AdvisorContractError("advisor changed local-only metadata")
            payload[key] = copy.deepcopy(original[key])
    originals = {(e["name"], f["name"]): f for e in original["entities"] for f in e["fields"]}
    projections = {(e["name"], f["name"]): f for e in projected["entities"] for f in e["fields"]}
    for entity in payload["entities"]:
        for field in entity["fields"]:
            field_key = (entity["name"], field["name"])
            if field_key not in originals:
                continue  # Schema identity is checked by the caller.
            original_field, projected_field = originals[field_key], projections[field_key]
            if original_field.get("semantic_type") != projected_field.get("semantic_type"):
                if (field.get("semantic_type") != projected_field.get("semantic_type")
                        or (projected_field["sensitive"] and not field["sensitive"])
                        or (projected_field["is_identifier"] and not field["is_identifier"])):
                    raise AdvisorContractError("advisor changed local-only semantic metadata")
                field["semantic_type"] = original_field.get("semantic_type")
            before, safe = original_field["distribution"], projected_field["distribution"]
            if before != safe:
                # Only opaque local configuration and lexical date details are immutable here.
                if before.get("kind") in {"synthetic_identifier", "masked_patterns", "date_range", "datetime_range"}:
                    if field["distribution"] != safe:
                        raise AdvisorContractError("advisor changed local-only distribution metadata")
                    field["distribution"] = copy.deepcopy(before)
    for index, constraint in enumerate(payload.get("constraints", [])):
        if index < len(projected["constraints"]) and constraint == projected["constraints"][index]:
            payload["constraints"][index] = copy.deepcopy(original["constraints"][index])


def _provider_safe_request(
    request: AdvisorRequest,
    *, category_label_prefix: str = "__apa_provider_category",
) -> tuple[dict[str, Any], dict[tuple[str, str, str], Any]]:
    payload = request.model_dump(mode="json")
    restorations = _ProviderRestorations()
    restorations.original = copy.deepcopy(payload["baseline_spec"])
    for dataset_name in ("profile", "baseline_spec"):
        _semantic_projection(payload[dataset_name])
    restorations.projected = copy.deepcopy(payload["baseline_spec"])
    local_fields = {
        (entity.name, field.name)
        for dataset in (request.profile, request.baseline_spec)
        for entity in dataset.entities for field in entity.fields
        if field.distribution.get("kind") == "categorical"
    }
    replacements: dict[tuple[str, str, str], str] = {}
    used_values = {
        _scalar_identity(category.get("value"))
        for dataset_name in ("profile", "baseline_spec")
        for entity in payload[dataset_name]["entities"]
        for field in entity["fields"]
        for category in field.get("distribution", {}).get("categories", [])
        if isinstance(category, dict)
    }
    field_positions = {
        (entity["name"], field["name"]): (entity_index, field_index)
        for entity_index, entity in enumerate(payload["profile"]["entities"])
        for field_index, field in enumerate(entity["fields"])
    }
    category_indexes: dict[tuple[str, str], int] = {}
    for dataset_name in ("profile", "baseline_spec"):
        for entity in payload[dataset_name]["entities"]:
            for field in entity["fields"]:
                field_key = (entity["name"], field["name"])
                if field_key not in local_fields:
                    continue
                categories = field.get("distribution", {}).get("categories", [])
                for category in categories:
                    if not isinstance(category, dict):
                        continue
                    value = category.get("value")
                    key = (*field_key, _scalar_identity(value))
                    placeholder = replacements.get(key)
                    if placeholder is None:
                        entity_index, field_index = field_positions[field_key]
                        category_index = category_indexes.get(field_key, 0)
                        category_indexes[field_key] = category_index + 1
                        placeholder = (
                            f"{category_label_prefix}_"
                            f"e{entity_index}_f{field_index}_c{category_index}__"
                        )
                        suffix = 1
                        while _scalar_identity(placeholder) in used_values:
                            placeholder = (
                                f"{category_label_prefix}_"
                                f"e{entity_index}_f{field_index}_c{category_index}_"
                                f"{suffix}__"
                            )
                            suffix += 1
                        replacements[key] = placeholder
                        restorations[(*field_key, _scalar_identity(placeholder))] = (
                            value
                        )
                        used_values.add(_scalar_identity(placeholder))
                    category["value"] = placeholder
        _replace_constraint_literals(
            payload[dataset_name],
            replacements,
            strict_fields=set(field_positions),
        )
    return payload, restorations


def _restore_local_categories(
    proposal: AdvisorProposal,
    restorations: dict[tuple[str, str, str], Any],
) -> None:
    payload = proposal.dataset_spec.model_dump(mode="python")
    for entity in payload["entities"]:
        for field in entity["fields"]:
            categories = field.get("distribution", {}).get("categories", [])
            for category in categories:
                if not isinstance(category, dict):
                    continue
                key = (
                    entity["name"],
                    field["name"],
                    _scalar_identity(category.get("value")),
                )
                if key in restorations:
                    category["value"] = restorations[key]
    _replace_constraint_literals(payload, restorations)
    if isinstance(restorations, _ProviderRestorations):
        _restore_semantic_metadata(payload, restorations)
    restored = type(proposal.dataset_spec).model_validate(payload)
    proposal.dataset_spec = restored


def _replace_constraint_literals(
    dataset: dict[str, Any],
    replacements: Mapping[tuple[str, str, str], Any],
    *,
    strict_fields: set[tuple[str, str]] | None = None,
) -> None:
    for constraint in dataset.get("constraints", []):
        condition = constraint.get("condition")
        if not isinstance(condition, dict):
            continue
        field = condition.get("field")
        if not isinstance(field, str):
            continue
        for predicate in ("equals", "not_equals"):
            if predicate in condition:
                key = (
                    constraint["entity"],
                    field,
                    _scalar_identity(condition[predicate]),
                )
                if strict_fields and (constraint["entity"], field) in strict_fields and key not in replacements:
                    raise AdvisorContractError("advisor constraint contains an unrepresented categorical value")
                condition[predicate] = replacements.get(key, condition[predicate])
        values = condition.get("in_values")
        if (
            "in_values" in condition
            and strict_fields
            and (constraint["entity"], field) in strict_fields
            and not isinstance(values, list)
        ):
            raise AdvisorContractError("advisor constraint uses an invalid condition")
        if isinstance(values, list):
            if strict_fields and (constraint["entity"], field) in strict_fields and any(
                (constraint["entity"], field, _scalar_identity(value)) not in replacements
                for value in values
            ):
                raise AdvisorContractError("advisor constraint contains an unrepresented categorical value")
            condition["in_values"] = [
                replacements.get(
                    (constraint["entity"], field, _scalar_identity(value)),
                    value,
                )
                for value in values
            ]


def _scalar_identity(value: Any) -> str:
    if value is not None and not isinstance(value, (str, int, float, bool)):
        raise AdvisorContractError("advisor category uses a non-scalar value")
    if isinstance(value, float) and not math.isfinite(value):
        raise AdvisorContractError("advisor category uses a non-finite value")
    return json.dumps(value, ensure_ascii=True, allow_nan=False)


