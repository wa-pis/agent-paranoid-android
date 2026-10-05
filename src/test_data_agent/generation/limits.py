"""Allocation estimates shared by deterministic generation and I/O preflight."""

import json
from typing import Any

from test_data_agent.core.dataset import DatasetSpec
from test_data_agent.core.constraint import ConstraintStatus, ConstraintType
from test_data_agent.core.limits import GenerationBudget, enforce_business_rule_evaluations


def estimate_dataset_output_bytes(spec: DatasetSpec) -> int:
    total = len(spec.model_dump_json().encode("utf-8")) * 2 + 65_536
    for entity in spec.entities:
        row_bytes = 2
        for field in entity.fields:
            row_bytes += len(field.name.encode("utf-8")) + estimate_field_output_bytes(field) + 8
        total += entity.row_count * row_bytes * 2
    return total


def estimate_field_output_bytes(field: Any) -> int:
    if field.is_identifier:
        return len(field.name.encode("utf-8")) + 64
    if field.sensitive:
        return 128
    if field.data_type != "string":
        return 64
    distribution = field.distribution or {}
    if distribution.get("kind") == "categorical":
        categories = distribution.get("categories") or []
        return max(
            (
                len(json.dumps(category.get("value"), default=str).encode("utf-8"))
                for category in categories
            ),
            default=16,
        )
    maximum = int(distribution.get("max_length", 12))
    return max(1, maximum) + 4



def enforce_dataset_rule_work(
    spec: DatasetSpec,
    *,
    budget: GenerationBudget,
    row_counts: dict[str, int] | None = None,
) -> None:
    """Reject obvious rule amplification before row generation or rule execution.

    Runtime checkpoints additionally charge actual graph edges and iterations.
    """
    counts = row_counts if row_counts is not None else {
        entity.name: entity.row_count for entity in spec.entities
    }
    estimated = len(spec.constraints) + len(spec.relationships)
    for constraint in spec.constraints:
        budget.check("rule work preflight")
        if constraint.status == ConstraintStatus.REJECTED:
            continue
        rows = counts.get(constraint.entity, 0)
        if constraint.type == ConstraintType.AGGREGATE_MAPPING:
            rows += counts.get(constraint.target_entity or "", 0)
            estimated += len(spec.relationships)
        cost = max(1, len(constraint.fields))
        if constraint.type == ConstraintType.CONDITIONAL_REQUIRED:
            cost += len((constraint.condition or {}).get("in_values") or [])
        estimated += rows * cost
        enforce_business_rule_evaluations(estimated)
    for relationship in spec.relationships:
        budget.check("rule work preflight")
        if relationship.status == "rejected":
            continue
        estimated += counts.get(relationship.parent_entity, 0)
        estimated += 2 * counts.get(relationship.child_entity, 0)
        enforce_business_rule_evaluations(estimated)
    enforce_business_rule_evaluations(estimated)
