"""Provider-neutral, field-scoped local category projection and restoration."""

from __future__ import annotations

import json
from collections.abc import Mapping
from typing import Any

from test_data_agent.advisor import AdvisorContractError, AdvisorProposal, AdvisorRequest


def _provider_safe_request(
    request: AdvisorRequest,
) -> tuple[dict[str, Any], dict[tuple[str, str, str], Any]]:
    payload = request.model_dump(mode="json")
    local_fields = {
        (item.entity, item.field)
        for item in (
            *request.profile.local_category_fields,
            *request.baseline_spec.local_category_fields,
        )
    }
    replacements: dict[tuple[str, str, str], str] = {}
    restorations: dict[tuple[str, str, str], Any] = {}
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
                            "__apa_provider_category_"
                            f"e{entity_index}_f{field_index}_c{category_index}__"
                        )
                        suffix = 1
                        while _scalar_identity(placeholder) in used_values:
                            placeholder = (
                                "__apa_provider_category_"
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
            strict_fields=local_fields,
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
    return json.dumps(value, ensure_ascii=True, allow_nan=False)


