"""Private bounded preparation and atomic allocation of synthetic relationships."""
from __future__ import annotations

import hashlib
import json
import random
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from test_data_agent.core.distribution import SyntheticIdentifierDistribution
from test_data_agent.core.fingerprints import model_fingerprint
from test_data_agent.core.limits import (
    GenerationBudget, enforce_row_count_limit, max_input_rows,
    enforce_input_cell_count, enforce_output_payload_size, max_input_cell_chars,
)
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


@dataclass(frozen=True)
class RelationalScenarioObservation:
    edge: tuple[str, str, str, str]
    requested_orphan_count: int
    observed_orphan_count: int
    requested_fanout_counts: tuple[int, ...] | None
    observed_fanout_counts: tuple[int, ...] | None
    eligible_child_count: int
    null_child_count: int
    valid: bool
    expectations_met: bool


def _observe_scenario(
    rows: dict[str, list[dict[str, Any]]], scenario: RelationalScenario,
    *, budget: GenerationBudget,
) -> RelationalScenarioObservation:
    parents = [row[scenario.parent_field] for row in budget.iter_rule_work(rows[scenario.parent_entity])]
    ordinals = {value: index for index, value in budget.iter_rule_work(enumerate(parents)) if value is not None}
    distinct = len(ordinals) == sum(value is not None for value in budget.iter_rule_work(parents))
    counts = [0] * len(parents)
    nulls = orphans = eligible = 0
    for row in budget.iter_rule_work(rows[scenario.child_entity]):
        value = row[scenario.child_field]
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


def _allocate_scenario(
    rows: dict[str, list[dict[str, Any]]], spec: DatasetSpec,
    scenario: RelationalScenario, *, seed: int, budget: GenerationBudget,
) -> None:
    parents = [row[scenario.parent_field] for row in budget.iter_rule_work(rows[scenario.parent_entity])]
    children = [row for row in budget.iter_rule_work(rows[scenario.child_entity]) if row[scenario.child_field] is not None]
    eligible = len(children)
    if scenario.orphan_count > eligible or (scenario.fanout_counts is not None and
            sum(scenario.fanout_counts) + scenario.orphan_count != eligible):
        raise RelationalScenarioError("relational scenario totals do not match actual eligible children")
    parent_keys = {value for value in budget.iter_rule_work(parents) if value is not None}
    if scenario.fanout_counts is not None:
        if len(parent_keys) != sum(value is not None for value in budget.iter_rule_work(parents)):
            raise RelationalScenarioError("fan-out requires distinct generated parent keys")
        if any(value is None and count for value, count in budget.iter_rule_work(zip(parents, scenario.fanout_counts))):
            raise RelationalScenarioError("fan-out cannot assign a null parent key")
    edge_bytes = json.dumps([seed, scenario.edge], separators=(",", ":")).encode()
    rng = random.Random(int.from_bytes(hashlib.sha256(edge_bytes).digest(), "big"))
    # Shuffle explicitly so every allocation step consumes the invocation allowance.
    for index in budget.iter_rule_work(range(eligible - 1, 0, -1)):
        other = rng.randrange(index + 1)
        children[index], children[other] = children[other], children[index]
    relationship = next(edge for edge in spec.relationships if
                        (edge.parent_entity, edge.parent_field, edge.child_entity, edge.child_field) == scenario.edge)
    unique = relationship.relationship_type == RelationshipType.ONE_TO_ONE or spec.entity(scenario.child_entity).primary_key == scenario.child_field
    valid_count = eligible - scenario.orphan_count
    if valid_count and (not parent_keys or unique and valid_count > len(parent_keys)):
        raise RelationalScenarioError("generated parent capacity cannot satisfy the scenario")
    cursor = 0
    if scenario.fanout_counts is not None:
        for value, count in budget.iter_rule_work(zip(parents, scenario.fanout_counts)):
            for _ in budget.iter_rule_work(range(count)):
                children[cursor][scenario.child_field] = value
                cursor += 1
    else:
        values = list(dict.fromkeys(value for value in budget.iter_rule_work(parents) if value is not None))
        for cursor in budget.iter_rule_work(range(valid_count)):
            children[cursor][scenario.child_field] = values[cursor % len(values)]
    candidate = 0
    integer_keys = spec.entity(scenario.child_entity).field(scenario.child_field).data_type == "integer"
    for index in budget.iter_rule_work(range(valid_count, eligible)):
        while True:
            budget.consume_rule_work()
            missing: int | str = -candidate if integer_keys else f"synthetic_{-candidate}"
            candidate += 1
            if missing not in parent_keys:
                break
        children[index][scenario.child_field] = missing


def apply_prepared_relational_scenarios(
    rows: dict[str, list[dict[str, Any]]], spec: DatasetSpec,
    plan: PreparedRelationalScenarios, *, seed: int, budget: GenerationBudget,
) -> tuple[RelationalScenarioObservation, ...]:
    """Allocate on a bounded key preview; commit only a completely reconciled snapshot."""
    from test_data_agent.generation.constraint_solver import _ordered_relationships, apply_relationships
    from test_data_agent.validation.relationship_validator import validate_relationships, RelationshipMetrics

    verify_relational_scenario_binding(plan, spec, seed=seed, budget=budget)
    if not plan.scenarios:
        return ()
    if set(rows) != {entity.name for entity in spec.entities}:
        raise RelationalScenarioError("relational scenario requires a complete generated snapshot")
    fields: dict[str, set[str]] = {entity.name: set() for entity in spec.entities}
    for edge in budget.iter_rule_work(spec.relationships):
        if edge.status != "rejected":
            fields[edge.parent_entity].add(edge.parent_field)
            fields[edge.child_entity].add(edge.child_field)
    preview: dict[str, list[dict[str, Any]]] = {}
    saved: list[tuple[dict[str, Any], str, Any, dict[str, Any]]] = []
    cells = payload = 0
    for entity in budget.iter_rule_work(spec.entities):
        if len(rows[entity.name]) != entity.row_count:
            raise RelationalScenarioError("relational scenario generated sizes do not match the prepared spec")
        preview[entity.name] = []
        for row in budget.iter_rule_work(rows[entity.name]):
            if type(row) is not dict:
                raise RelationalScenarioError("relational scenario requires ordinary generated row dictionaries")
            projected: dict[str, Any] = {}
            for name in budget.iter_rule_work(sorted(fields[entity.name])):
                field = entity.field(name)
                if name not in row:
                    raise RelationalScenarioError("relational scenario generated key is missing")
                value = row[name]
                if value is None:
                    accepted = field.nullable
                else:
                    accepted = type(value) is int if field.data_type == "integer" else type(value) is str and bool(value)
                if not accepted or (type(value) is str and len(value) > max_input_cell_chars()) or (type(value) is int and value.bit_length() > 16384):
                    raise RelationalScenarioError("relational scenario generated key has an unsupported scalar type or size")
                cells += 1
                payload += 128 + len(name.encode()) + (len(value.encode()) if type(value) is str else 8192 if type(value) is int else 4)
                enforce_input_cell_count(cells, label="relational key preview")
                enforce_output_payload_size(payload, label="relational key preview")
                projected[name] = value
                saved.append((row, name, value, projected))
            preview[entity.name].append(projected)
    selected = {item.edge: item for item in plan.scenarios}
    for edge in budget.iter_rule_work(_ordered_relationships(spec, budget=budget)):
        key = (edge.parent_entity, edge.parent_field, edge.child_entity, edge.child_field)
        if key in selected:
            _allocate_scenario(preview, spec, selected[key], seed=seed, budget=budget)
        else:
            apply_relationships(preview, spec.model_copy(update={"relationships": [edge]}), budget=budget)
    evidence = tuple(_observe_scenario(preview, item, budget=budget) for item in budget.iter_rule_work(plan.scenarios))
    metrics: list[RelationshipMetrics] = []
    errors = validate_relationships(preview, spec, budget=budget, metrics=metrics)
    for item in budget.iter_rule_work(plan.scenarios):
        child = spec.entity(item.child_entity)
        if child.primary_key == item.child_field:
            values = [row[item.child_field] for row in budget.iter_rule_work(preview[item.child_entity])]
            if len(set(values)) != len(values) or None in values:
                raise RelationalScenarioError("relational scenario violates generated child primary-key uniqueness")
    expected_errors = sum(item.orphan_count for item in plan.scenarios)
    if not all(item.expectations_met for item in evidence) or len(errors) != expected_errors:
        raise RelationalScenarioError("relational scenario snapshot does not satisfy the declared relationships")
    for metric in budget.iter_rule_work(metrics):
        key = (metric.parent_entity, metric.parent_field, metric.child_entity, metric.child_field)
        expected = selected[key].orphan_count if key in selected else 0
        if metric.checked_references - metric.resolved_references != expected:
            raise RelationalScenarioError("relational scenario changed an unscoped relationship")
    verify_relational_scenario_binding(plan, spec, seed=seed, budget=budget)
    for row, name, old, projected in budget.iter_rule_work(saved):
        if name not in row or row[name] != old:
            raise RelationalScenarioError("relational scenario generated snapshot became stale")
    committed = 0
    try:
        for row, name, old, projected in budget.iter_rule_work(saved):
            row[name] = projected[name]
            committed += 1
        budget.check("relational scenario commit")
    except BaseException:
        # Rollback cannot depend on the allowance that just expired.
        for index in range(committed):
            row, name, old, _ = saved[index]
            row[name] = old
        raise
    return evidence
