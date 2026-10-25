"""Private execution uses only fictional generated key domains."""
from copy import deepcopy

import pytest

from test_data_agent.core.limits import GenerationBudget, GenerationLimitError
from test_data_agent.generation.relational_scenarios import (
    RelationalScenarioError, apply_prepared_relational_scenarios,
)
from tests.test_relational_scenario_preflight import prepare, scenario, spec


def rows():
    return {"parents": [{"key": 100 + i} for i in range(3)],
            "children": [{"parent_key": 200 + i} for i in range(6)]}


def execute(data, source, declarations, *, seed=7, budget=None):
    plan = prepare(source, declarations, seed=seed)
    return apply_prepared_relational_scenarios(data, source, plan, seed=seed,
                                               budget=budget or GenerationBudget())


def test_exact_orphans_and_nonuniform_fanout_replay_with_count_only_evidence():
    source = spec(mode="mixed")
    original = rows()
    data = deepcopy(original)
    declared = [scenario(orphan_count=2, fanout_counts=(3, 1, 0))]
    evidence = execute(data, source, declared)
    again = deepcopy(original)
    assert evidence == execute(again, source, declared)
    assert data == again
    item = evidence[0]
    assert item.requested_orphan_count == item.observed_orphan_count == 2
    assert item.observed_fanout_counts == (3, 1, 0)
    assert item.expectations_met and not item.valid
    assert item.eligible_child_count == 6 and item.null_child_count == 0
    assert all(str(value) not in repr(evidence) for value in (100, 101, 102))
    different = deepcopy(original)
    execute(different, source, declared, seed=8)
    assert different != data


def test_one_to_one_allows_more_children_when_exact_orphans_cover_excess():
    source = spec(mode="mixed", one_to_one=True)
    data = rows()
    evidence = execute(data, source, [scenario(orphan_count=3, fanout_counts=(1, 1, 1))])
    assert evidence[0].observed_orphan_count == 3
    assert len({row["parent_key"] for row in data["children"]}) == 6
    assert evidence[0].expectations_met


def test_all_null_child_mask_is_preserved_with_zero_allocation():
    source = spec(nullable=True, null_ratio=1)
    data = rows()
    for row in data["children"]:
        row["parent_key"] = None
    before = deepcopy(data)
    evidence = execute(data, source, [scenario(fanout_counts=(0, 0, 0))])
    assert data == before
    assert evidence[0].observed_orphan_count == 0
    assert evidence[0].null_child_count == 6
    assert evidence[0].valid and evidence[0].expectations_met


@pytest.mark.parametrize("failure", ["duplicates", "missing_parent", "wrong_type", "missing_child"])
def test_bad_generated_snapshot_rejects_without_mutation(failure):
    source = spec()
    data = rows()
    if failure == "duplicates":
        data["parents"][1]["key"] = data["parents"][0]["key"]
    elif failure == "missing_parent":
        data["parents"].pop()
    elif failure == "missing_child":
        del data["children"][0]["parent_key"]
    else:
        data["parents"][0]["key"] = True
    before = deepcopy(data)
    with pytest.raises(RelationalScenarioError):
        execute(data, source, [scenario(fanout_counts=(1, 2, 3))])
    assert data == before


def test_actual_nullable_eligibility_rejects_a_static_unknown_total():
    source = spec(nullable=True, null_ratio=0.5)
    data = rows()
    for row in data["children"]:
        row["parent_key"] = None
    before = deepcopy(data)
    with pytest.raises(RelationalScenarioError, match="eligible"):
        execute(data, source, [scenario(fanout_counts=(1, 1, 1))])
    assert data == before


def test_complete_preflight_and_commit_share_deadline_with_rollback():
    source = spec()
    data = rows()
    before = deepcopy(data)
    budget = GenerationBudget(max_seconds=1, clock=lambda: 0.0 if data == before else 2.0)
    with pytest.raises(GenerationLimitError):
        execute(data, source, [scenario(fanout_counts=(1, 2, 3))], budget=budget)
    assert data == before


def test_empty_declaration_does_not_reassign_legacy_rows():
    source = spec()
    data = rows()
    before = deepcopy(data)
    assert execute(data, source, []) == ()
    assert data == before


def test_dependency_order_updates_unscoped_descendants_of_selected_keys():
    source = spec()
    leaf = source.entities[1].model_copy(deep=True)
    leaf.name = "leaves"
    source.entities.append(leaf)
    edge = source.relationships[0].model_copy(update={
        "parent_entity": "children", "parent_field": "parent_key", "child_entity": "leaves"})
    source.relationships.insert(0, edge)
    data = rows()
    data["leaves"] = [{"parent_key": 300 + index} for index in range(6)]
    evidence = execute(data, source, [scenario(fanout_counts=(1, 2, 3))])
    assert evidence[0].expectations_met
    assert {row["parent_key"] for row in data["leaves"]} <= {row["parent_key"] for row in data["children"]}


def test_late_second_scenario_failure_leaves_every_original_key_unchanged():
    source = spec(nullable=True, null_ratio=0.5)
    other = source.entities[1].model_copy(deep=True)
    other.name = "other_children"
    source.entities.append(other)
    source.relationships.append(source.relationships[0].model_copy(update={"child_entity": other.name}))
    data = rows()
    data[other.name] = [{"parent_key": None} for _ in range(6)]
    before = deepcopy(data)
    declarations = [scenario(fanout_counts=(1, 2, 3)),
                    scenario(fanout_counts=(1, 2, 3)).model_copy(update={"child_entity": other.name})]
    with pytest.raises(RelationalScenarioError, match="eligible"):
        execute(data, source, declarations)
    assert data == before


def test_string_orphans_use_only_disjoint_synthetic_identifier_namespace():
    source = spec(mode="mixed")
    for entity in source.entities:
        entity.fields[0].data_type = "string"
    data = rows()
    for row in data["parents"]:
        row["key"] = f"synthetic_{row['key']}"
    for row in data["children"]:
        row["parent_key"] = f"synthetic_{row['parent_key']}"
    evidence = execute(data, source, [scenario(orphan_count=2, fanout_counts=(3, 1, 0))])
    assert evidence[0].observed_orphan_count == 2
    assert all(row["parent_key"].startswith("synthetic_") for row in data["children"])


def test_key_preview_obeys_cell_limit_without_partial_mutation(monkeypatch):
    source = spec()
    data = rows()
    before = deepcopy(data)
    monkeypatch.setenv("TEST_DATA_AGENT_MAX_INPUT_CELLS", "2")
    with pytest.raises(ValueError, match="relational key preview"):
        execute(data, source, [scenario(fanout_counts=(1, 2, 3))])
    assert data == before


def test_rejected_duplicate_relationship_does_not_select_scenario_cardinality():
    payload = spec().model_dump(mode="json")
    payload["relationships"].insert(0, {**payload["relationships"][0],
        "status": "rejected", "relationship_type": "one_to_one"})
    source = type(spec()).model_validate(payload)
    data = rows()
    evidence = execute(data, source, [scenario(fanout_counts=(1, 2, 3))])
    assert evidence[0].expectations_met
    assert [sum(child["parent_key"] == parent["key"] for child in data["children"])
            for parent in data["parents"]] == [1, 2, 3]
