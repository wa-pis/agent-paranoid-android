"""Bounded metadata-only preflight for future explicit relational execution."""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import TYPE_CHECKING

from test_data_agent.core.distribution import SyntheticIdentifierDistribution
from test_data_agent.core.fingerprints import model_fingerprint
from test_data_agent.core.limits import GenerationBudget, enforce_row_count_limit, max_input_rows
from test_data_agent.core.relationship import RelationshipType
from test_data_agent.core.relational_scenario import RelationalScenario
from test_data_agent.core.settings import GenerationMode, MIN_GENERATION_SEED, MAX_GENERATION_SEED
from test_data_agent.rules.models import (
    ConditionalAllowedValuesRule, ConditionalRequiredRule, ForeignKeyRule,
    FormulaRule, TemporalOrderingRule,
)

if TYPE_CHECKING:
    from test_data_agent.core.dataset import DatasetSpec

MAX_RELATIONAL_SCENARIOS = 1_000


class RelationalScenarioError(ValueError):
    """A source-free declaration, allocation or binding failure."""


@dataclass(frozen=True)
class PreparedRelationalScenarios:
    spec_sha256: str
    sizes_sha256: str
    scenarios_sha256: str
    seed: int
    scenarios: tuple[RelationalScenario, ...]


def _sizes_hash(spec: DatasetSpec, budget: GenerationBudget) -> str:
    sizes = []
    for entity in budget.iter_rule_work(spec.entities):
        enforce_row_count_limit(entity.row_count)
        sizes.append((entity.name, entity.row_count))
    return hashlib.sha256(json.dumps(sorted(sizes), separators=(",", ":")).encode()).hexdigest()


def prepare_relational_scenarios(
    spec: DatasetSpec, scenarios: tuple[RelationalScenario, ...], *, seed: int,
    budget: GenerationBudget,
) -> PreparedRelationalScenarios:
    """Use the effective spec after count overrides/load-size resolution; never mutate it."""
    budget.check("relational scenario preflight")
    if type(seed) is not int or not MIN_GENERATION_SEED <= seed <= MAX_GENERATION_SEED:
        raise RelationalScenarioError("relational scenario seed must be a signed 64-bit integer")
    if len(scenarios) > MAX_RELATIONAL_SCENARIOS:
        raise RelationalScenarioError("relational scenario count exceeds the bounded limit")
    sizes_sha256 = _sizes_hash(spec, budget)
    active = [edge for edge in budget.iter_rule_work(spec.relationships) if edge.status != "rejected"]
    selected: set[tuple[str, str]] = set()
    for scenario in budget.iter_rule_work(scenarios):
        target = (scenario.child_entity, scenario.child_field)
        matches = [edge for edge in budget.iter_rule_work(active)
                   if (edge.parent_entity, edge.parent_field, edge.child_entity, edge.child_field) == scenario.edge]
        writers = sum((edge.child_entity, edge.child_field) == target for edge in budget.iter_rule_work(active))
        if len(matches) != 1 or writers != 1 or target in selected:
            raise RelationalScenarioError("relational scenario requires one unambiguous active edge per child field")
        selected.add(target)
        parent = spec.entity(scenario.parent_entity)
        child = spec.entity(scenario.child_entity)
        parent_field = parent.field(scenario.parent_field)
        child_field = child.field(scenario.child_field)
        if parent_field.data_type != child_field.data_type or parent_field.data_type not in {"integer", "string"}:
            raise RelationalScenarioError("relational scenarios require matching integer or string key types")
        if scenario.orphan_count and spec.generation_settings.mode not in {GenerationMode.MIXED, GenerationMode.NEGATIVE}:
            raise RelationalScenarioError("controlled orphans require mixed or negative mode")
        if spec.generation_settings.invalid_ratio:
            raise RelationalScenarioError("relational scenarios cannot combine an unscoped invalid ratio")
        if spec.business_rules is not None and spec.generation_settings.mode == GenerationMode.NEGATIVE:
            raise RelationalScenarioError("relational scenarios cannot combine negative business-rule injection")
        known_eligible = (0 if child_field.nullable and child_field.null_ratio == 1 else
                          child.row_count if not child_field.nullable or child_field.null_ratio == 0 else None)
        maximum_eligible = child.row_count if known_eligible is None else known_eligible
        if scenario.orphan_count > maximum_eligible:
            raise RelationalScenarioError("controlled orphan count exceeds eligible children")
        unique_children = matches[0].relationship_type == RelationshipType.ONE_TO_ONE or child.primary_key == child_field.name
        pool = parent_field.typed_distribution
        parent_capacity = min(parent.row_count, pool.pool_size) if isinstance(pool, SyntheticIdentifierDistribution) and pool.pool_size is not None else parent.row_count
        if parent_field.nullable and parent_field.null_ratio == 1:
            parent_capacity = 0
        if scenario.fanout_counts is not None:
            if len(scenario.fanout_counts) != parent.row_count or len(scenario.fanout_counts) > max_input_rows():
                raise RelationalScenarioError("fan-out counts must match bounded generated parent ordinals")
            if parent_capacity < parent.row_count and any(scenario.fanout_counts):
                raise RelationalScenarioError("fan-out requires distinct non-null generated parent keys")
            total = scenario.orphan_count
            for count in budget.iter_rule_work(scenario.fanout_counts):
                if unique_children and count > 1:
                    raise RelationalScenarioError("fan-out conflicts with unique child keys")
                total += count
            if total > maximum_eligible or known_eligible is not None and total != known_eligible:
                raise RelationalScenarioError("fan-out and orphan totals must match eligible children")
        if known_eligible is not None and (unique_children and known_eligible - scenario.orphan_count > parent_capacity
                                          or parent_capacity == 0 and known_eligible > scenario.orphan_count):
            raise RelationalScenarioError("generated parent capacity cannot satisfy the scenario")
        _reject_key_writers(spec, scenario, budget)
    fingerprint = model_fingerprint(spec)
    budget.check("relational scenario binding")
    scenario_bytes = json.dumps([item.model_dump(mode="json") for item in scenarios], sort_keys=True, separators=(",", ":")).encode()
    return PreparedRelationalScenarios(fingerprint, sizes_sha256, hashlib.sha256(scenario_bytes).hexdigest(), seed, scenarios)


def verify_relational_scenario_binding(
    plan: PreparedRelationalScenarios, spec: DatasetSpec, *, seed: int, budget: GenerationBudget,
) -> None:
    budget.check("relational scenario binding")
    scenario_bytes = json.dumps([item.model_dump(mode="json") for item in plan.scenarios], sort_keys=True, separators=(",", ":")).encode()
    if (type(seed) is not int or seed != plan.seed or model_fingerprint(spec) != plan.spec_sha256
            or _sizes_hash(spec, budget) != plan.sizes_sha256
            or hashlib.sha256(scenario_bytes).hexdigest() != plan.scenarios_sha256):
        raise RelationalScenarioError("relational scenario binding is stale; prepare the effective spec again")
    budget.check("relational scenario binding")


def _reject_key_writers(spec: DatasetSpec, scenario: RelationalScenario, budget: GenerationBudget) -> None:
    keys = {(scenario.parent_entity, scenario.parent_field), (scenario.child_entity, scenario.child_field)}
    for constraint in budget.iter_rule_work(spec.constraints):
        if constraint.status == "rejected":
            continue
        if any((constraint.entity, name) in keys for name in budget.iter_rule_work(constraint.fields)) or (constraint.target_entity, constraint.target_field) in keys:
            raise RelationalScenarioError("relational scenario conflicts with a native key constraint")
    rules = spec.business_rules
    if rules is None:
        return
    for field_rule in budget.iter_rule_work(rules.field_rules):
        if (field_rule.table, field_rule.field) in keys:
            raise RelationalScenarioError("relational scenario conflicts with a key field rule")
    for rule in budget.iter_rule_work(rules.row_rules):
        if isinstance(rule, (FormulaRule, ConditionalAllowedValuesRule)):
            fields = [rule.field]
        elif isinstance(rule, ConditionalRequiredRule):
            fields = rule.required_fields
        elif isinstance(rule, TemporalOrderingRule):
            fields = [rule.end_field]
        else:
            fields = []
        if any((rule.table, name) in keys for name in budget.iter_rule_work(fields)):
            raise RelationalScenarioError("relational scenario conflicts with a row-rule key target")
    for cross_rule in budget.iter_rule_work(rules.cross_table_rules):
        if isinstance(cross_rule, ForeignKeyRule) and scenario.orphan_count and (cross_rule.child_table, cross_rule.child_field) in keys:
            raise RelationalScenarioError("controlled orphans conflict with a foreign-key business check")
    for weighted_rule in budget.iter_rule_work(rules.scenarios):
        for table, field_values in budget.iter_rule_work(weighted_rule.field_values.items()):
            if any((table, name) in keys for name in budget.iter_rule_work(field_values)):
                raise RelationalScenarioError("relational scenario conflicts with a weighted key assignment")
