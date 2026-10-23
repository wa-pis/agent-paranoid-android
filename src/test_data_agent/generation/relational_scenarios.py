"""Bounded atomic allocation of synthetic relationship scenarios."""
from __future__ import annotations

import hashlib
import json
import random
from typing import Any

from test_data_agent.core.dataset import DatasetSpec
from test_data_agent.core.limits import (
    GenerationBudget, enforce_input_cell_count, enforce_output_payload_size, max_input_cell_chars,
)
from test_data_agent.core.relationship import RelationshipType
from test_data_agent.core.relational_scenario import RelationalScenario, RelationalScenarioObservation
from test_data_agent.rules.relational_scenarios import (
    PreparedRelationalScenarios, RelationalScenarioError,
    prepare_relational_scenarios as prepare_relational_scenarios,
    verify_relational_scenario_binding,
)
from test_data_agent.validation.relational_scenarios import inspect_relational_scenarios


def _allocate_scenario(
    rows: dict[str, list[dict[str, Any]]], spec: DatasetSpec,
    scenario: RelationalScenario, *, seed: int, budget: GenerationBudget,
) -> None:
    parents = [row[scenario.parent_field] for row in budget.iter_rule_work(rows[scenario.parent_entity])]
    children = [row for row in budget.iter_rule_work(rows[scenario.child_entity]) if row[scenario.child_field] is not None]
    eligible = len(children)
    if scenario.orphan_count > eligible or (scenario.fanout_counts is not None and
            sum(budget.iter_rule_work(scenario.fanout_counts)) + scenario.orphan_count != eligible):
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
    relationship = next(edge for edge in budget.iter_rule_work(spec.relationships) if
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
        if type(missing) is str and len(missing) > max_input_cell_chars():
            raise RelationalScenarioError("synthetic orphan key exceeds configured cell size")
        children[index][scenario.child_field] = missing


def apply_prepared_relational_scenarios(
    rows: dict[str, list[dict[str, Any]]], spec: DatasetSpec,
    plan: PreparedRelationalScenarios, *, seed: int, budget: GenerationBudget,
) -> tuple[RelationalScenarioObservation, ...]:
    """Allocate on a bounded key preview; commit only a completely reconciled snapshot."""
    from test_data_agent.generation.constraint_solver import _ordered_relationships, apply_relationships

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
            payload += 64
            enforce_output_payload_size(payload, label="relational key preview")
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
    evidence = inspect_relational_scenarios(preview, spec, plan.scenarios, budget=budget)
    if not evidence.expectations_met:
        raise RelationalScenarioError("relational scenario snapshot does not satisfy the declared relationships")
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
    return evidence.observations
