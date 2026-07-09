"""Deterministic scenario assignment helpers for rule-driven generation."""

from __future__ import annotations

import random
from typing import Any

from test_data_agent.rules.models import ScenarioRule


def choose_scenario(scenarios: list[ScenarioRule], rng: random.Random) -> ScenarioRule | None:
    if not scenarios:
        return None
    total = sum(scenario.weight for scenario in scenarios)
    pick = rng.uniform(0, total)
    cursor = 0.0
    for scenario in scenarios:
        cursor += scenario.weight
        if pick <= cursor:
            return scenario
    return scenarios[-1]


def apply_scenarios(rows_by_table: dict[str, list[dict[str, Any]]], scenarios: list[ScenarioRule], seed: int) -> None:
    rng = random.Random(seed)
    for table, rows in rows_by_table.items():
        for row in rows:
            scenario = choose_scenario(scenarios, rng)
            if scenario is None:
                continue
            for field, value in scenario.field_values.get(table, {}).items():
                row[field] = value
