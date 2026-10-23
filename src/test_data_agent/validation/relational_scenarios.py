"""Count-only reconciliation of explicit generated relationship scenarios."""
from __future__ import annotations

from dataclasses import replace
from typing import Any

from pydantic import BaseModel

from test_data_agent.core.dataset import DatasetSpec
from test_data_agent.core.fingerprints import model_fingerprint
from test_data_agent.core.limits import GenerationBudget
from test_data_agent.core.relationship import RelationshipType
from test_data_agent.core.relational_scenario import RelationalScenario, RelationalScenarioObservation
from test_data_agent.rules.relational_scenarios import prepare_relational_scenarios
from test_data_agent.validation.relationship_validator import RelationshipMetrics, validate_relationships


class RelationalScenarioEvidence(BaseModel):
    spec_sha256: str
    sizes_sha256: str
    expectations_met: bool
    observations: tuple[RelationalScenarioObservation, ...]


def _observe_scenario(
    rows: dict[str, list[dict[str, Any]]], scenario: RelationalScenario,
    *, budget: GenerationBudget,
) -> RelationalScenarioObservation:
    parents = [row.get(scenario.parent_field) for row in budget.iter_rule_work(rows[scenario.parent_entity])]
    ordinals = {value: index for index, value in budget.iter_rule_work(enumerate(parents)) if value is not None}
    distinct = len(ordinals) == sum(value is not None for value in budget.iter_rule_work(parents))
    counts = [0] * len(parents)
    nulls = orphans = eligible = 0
    for row in budget.iter_rule_work(rows[scenario.child_entity]):
        value = row.get(scenario.child_field)
        if value is None:
            nulls += 1
            continue
        eligible += 1
        if value in ordinals:
            counts[ordinals[value]] += 1
        else:
            orphans += 1
    fanout = tuple(counts) if distinct else None
    return RelationalScenarioObservation(
        scenario.edge, scenario.orphan_count, orphans, scenario.fanout_counts,
        fanout, eligible, nulls, orphans == 0,
        orphans == scenario.orphan_count and (scenario.fanout_counts is None or fanout == scenario.fanout_counts),
    )



def inspect_relational_scenarios(
    rows: dict[str, list[dict[str, Any]]], spec: DatasetSpec,
    scenarios: tuple[RelationalScenario, ...], *, budget: GenerationBudget,
) -> RelationalScenarioEvidence:
    # This seed checks the declaration contract only, never asserts the generation seed.
    plan = prepare_relational_scenarios(spec, scenarios, seed=0, budget=budget)
    sizes_match = set(rows) == {entity.name for entity in spec.entities} and all(
        len(rows[entity.name]) == entity.row_count for entity in budget.iter_rule_work(spec.entities))
    if not sizes_match:
        return RelationalScenarioEvidence(spec_sha256=model_fingerprint(spec), sizes_sha256=plan.sizes_sha256,
                                          expectations_met=False, observations=())
    evidence = tuple(_observe_scenario(rows, item, budget=budget) for item in budget.iter_rule_work(scenarios))
    selected = {item.edge: item for item in scenarios}
    unique_targets = {(edge.child_entity, edge.child_field) for edge in spec.relationships
                      if edge.status != "rejected" and edge.relationship_type == RelationshipType.ONE_TO_ONE}
    revised = []
    for item in budget.iter_rule_work(evidence):
        child = spec.entity(item.edge[2])
        if (item.edge[2], item.edge[3]) in unique_targets or child.primary_key == item.edge[3]:
            values = [row.get(item.edge[3]) for row in budget.iter_rule_work(rows[item.edge[2]])
                      if row.get(item.edge[3]) is not None]
            if len(values) != len(set(values)):
                item = replace(item, valid=False, expectations_met=False)
        revised.append(item)
    evidence = tuple(revised)
    metrics: list[RelationshipMetrics] = []
    errors = validate_relationships(rows, spec, budget=budget, metrics=metrics)
    expected_errors = sum(item.orphan_count for item in scenarios)
    expectations_met = all(item.expectations_met for item in evidence) and len(errors) == expected_errors
    for metric in budget.iter_rule_work(metrics):
        key = (metric.parent_entity, metric.parent_field, metric.child_entity, metric.child_field)
        expected = selected[key].orphan_count if key in selected else 0
        expectations_met &= metric.checked_references - metric.resolved_references == expected
    for declared in budget.iter_rule_work(scenarios):
        child = spec.entity(declared.child_entity)
        if child.primary_key == declared.child_field:
            values = [row.get(declared.child_field) for row in budget.iter_rule_work(rows[declared.child_entity])]
            expectations_met &= len(set(values)) == len(values) and None not in values
    budget.check("relational scenario evidence")
    return RelationalScenarioEvidence(spec_sha256=model_fingerprint(spec), sizes_sha256=plan.sizes_sha256,
                                      expectations_met=expectations_met, observations=evidence)
