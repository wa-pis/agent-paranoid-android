"""Deterministic scenario assignment helpers for rule-driven generation."""

from __future__ import annotations

import random
from test_data_agent.core.limits import GenerationBudget

from typing import Any

from test_data_agent.rules.models import ScenarioRule


def choose_scenario(
    scenarios: list[ScenarioRule],
    rng: random.Random,
    *,
    budget: GenerationBudget | None = None,
) -> ScenarioRule | None:
    budget = budget or GenerationBudget()
    budget.check("deterministic rule entry")
    if not scenarios:
        return None
    total = sum(scenario.weight for scenario in budget.iter_rule_work(scenarios))
    pick = rng.uniform(0, total)
    cursor = 0.0
    for scenario in budget.iter_rule_work(scenarios):
        cursor += scenario.weight
        if pick <= cursor:
            return scenario
    return scenarios[-1]


def apply_scenarios(
    rows_by_table: dict[str, list[dict[str, Any]]],
    scenarios: list[ScenarioRule],
    seed: int,
    *,
    budget: GenerationBudget | None = None,
) -> None:
    budget = budget or GenerationBudget()
    budget.check("deterministic rule entry")
    rng = random.Random(seed)
    for table, rows in budget.iter_rule_work(rows_by_table.items()):
        for row in budget.iter_rule_work(rows):
            scenario = choose_scenario(scenarios, rng, budget=budget)
            if scenario is None:
                continue
            for field, value in budget.iter_rule_work(scenario.field_values.get(table, {}).items()):
                row[field] = value
