"""Only fictional metadata enters the relational scenario compiler."""
from dataclasses import replace

import pytest

from test_data_agent.core.dataset import DatasetSpec
from test_data_agent.core.limits import GenerationBudget, GenerationLimitError
from test_data_agent.core.relational_scenario import RelationalScenario
from test_data_agent.generation.relational_scenarios import (
    RelationalScenarioError, prepare_relational_scenarios, verify_relational_scenario_binding,
)


def spec(*, mode="valid", nullable=False, null_ratio=0, pool=None, one_to_one=False):
    return DatasetSpec.model_validate({
        "entities": [
            {"name": "parents", "row_count": 3, "primary_key": "key", "fields": [
                {"name": "key", "data_type": "integer", "is_identifier": True,
                 "distribution": {"kind": "synthetic_identifier", "pool_size": pool}}]},
            {"name": "children", "row_count": 6, "fields": [
                {"name": "parent_key", "data_type": "integer", "is_identifier": True,
                 "nullable": nullable, "null_ratio": null_ratio}]}],
        "relationships": [{"parent_entity": "parents", "parent_field": "key",
            "child_entity": "children", "child_field": "parent_key", "confidence": 1,
            "relationship_type": "one_to_one" if one_to_one else "many_to_one"}],
        "generation_settings": {"mode": mode},
    })


def scenario(**kwargs):
    return RelationalScenario(parent_entity="parents", parent_field="key",
                              child_entity="children", child_field="parent_key", **kwargs)


def prepare(source, declarations, *, seed=7):
    return prepare_relational_scenarios(source, tuple(declarations), seed=seed, budget=GenerationBudget())


def test_plan_binds_full_spec_resolved_sizes_scenario_and_explicit_seed_without_mutation():
    source = spec()
    before = source.model_dump_json()
    plan = prepare(source, [scenario(fanout_counts=(1, 2, 3))])
    assert before == source.model_dump_json()
    assert plan == prepare(source, [scenario(fanout_counts=(1, 2, 3))])
    verify_relational_scenario_binding(plan, source, seed=7, budget=GenerationBudget())
    assert all(len(value) == 64 for value in (plan.spec_sha256, plan.sizes_sha256, plan.scenarios_sha256))
    with pytest.raises(RelationalScenarioError, match="stale"):
        verify_relational_scenario_binding(plan, source, seed=8, budget=GenerationBudget())
    changed = replace(plan, scenarios=(scenario(fanout_counts=(2, 2, 2)),))
    with pytest.raises(RelationalScenarioError, match="stale"):
        verify_relational_scenario_binding(changed, source, seed=7, budget=GenerationBudget())
    source.entities[1].row_count = 7
    with pytest.raises(RelationalScenarioError, match="stale"):
        verify_relational_scenario_binding(plan, source, seed=7, budget=GenerationBudget())


@pytest.mark.parametrize("count", [True, "1", 1.5, -1])
def test_counts_are_strict_nonnegative_integers(count):
    with pytest.raises(ValueError):
        scenario(orphan_count=count)
    with pytest.raises(ValueError):
        scenario(fanout_counts=(count, 1, 1))


@pytest.mark.parametrize("seed", [True, "7", 1.5, 2**63, -(2**63)-1])
def test_seed_is_explicit_bounded_integer(seed):
    with pytest.raises(RelationalScenarioError):
        prepare(spec(), [scenario()], seed=seed)


@pytest.mark.parametrize("mode", ["valid", "edge", "load_test"])
def test_orphans_require_controlled_invalid_mode(mode):
    with pytest.raises(RelationalScenarioError, match="mixed or negative"):
        prepare(spec(mode=mode), [scenario(orphan_count=1)])


@pytest.mark.parametrize("mode", ["mixed", "negative"])
def test_controlled_exact_orphans_and_nonuniform_fanout_are_metadata_only(mode):
    plan = prepare(spec(mode=mode), [scenario(orphan_count=2, fanout_counts=(3, 1, 0))])
    assert plan.scenarios[0].orphan_count == 2
    assert plan.scenarios[0].fanout_counts == (3, 1, 0)


@pytest.mark.parametrize("counts", [(1, 2), (1, 2, 2), (1, 2, 4)])
def test_parent_width_and_exact_eligible_totals_reject(counts):
    with pytest.raises(RelationalScenarioError):
        prepare(spec(), [scenario(fanout_counts=counts)])


def test_all_null_children_accept_zero_allocation_and_reject_requested_orphans():
    source = spec(mode="mixed", nullable=True, null_ratio=1)
    assert prepare(source, [scenario(fanout_counts=(0, 0, 0))])
    with pytest.raises(RelationalScenarioError, match="eligible"):
        prepare(source, [scenario(orphan_count=1)])


def test_one_to_one_cannot_allocate_repeated_or_excessive_non_orphans():
    source = spec(mode="mixed", one_to_one=True)
    with pytest.raises(RelationalScenarioError, match="unique"):
        prepare(source, [scenario(orphan_count=3, fanout_counts=(2, 1, 0))])
    with pytest.raises(RelationalScenarioError, match="capacity"):
        prepare(source, [scenario(orphan_count=2)])
    assert prepare(source, [scenario(orphan_count=3, fanout_counts=(1, 1, 1))])


def test_key_pool_cannot_fake_distinct_parent_ordinals():
    source = spec()
    source.entities[0].primary_key = None
    source.entities[0].fields[0].distribution = {"kind": "synthetic_identifier", "pool_size": 2}
    with pytest.raises(RelationalScenarioError, match="distinct"):
        prepare(source, [scenario(fanout_counts=(1, 2, 3))])


def test_unknown_rejected_ambiguous_and_duplicate_targets_reject():
    source = spec()
    with pytest.raises(RelationalScenarioError):
        prepare(source, [scenario(), scenario()])
    source.relationships[0].status = "rejected"
    with pytest.raises(RelationalScenarioError):
        prepare(source, [scenario()])
    source.relationships[0].status = "inferred"
    source.relationships.append(source.relationships[0].model_copy())
    with pytest.raises(RelationalScenarioError):
        prepare(source, [scenario()])
    other = scenario().model_copy(update={"parent_field": "unknown"})
    with pytest.raises(RelationalScenarioError):
        prepare(spec(), [other])


def test_no_silent_ratio_precedence():
    source = spec(mode="mixed")
    source.generation_settings.invalid_ratio = 0.25
    with pytest.raises(RelationalScenarioError, match="unscoped"):
        prepare(source, [scenario(orphan_count=1)])


def test_key_rule_conflict_rejects_and_leaves_spec_unchanged():
    from test_data_agent.rules.models import BusinessRules
    source = spec()
    source.business_rules = BusinessRules(field_rules=[{"table": "children", "field": "parent_key", "required": True}])
    before = source.model_dump_json()
    with pytest.raises(RelationalScenarioError, match="key field"):
        prepare(source, [scenario(fanout_counts=(1, 2, 3))])
    assert source.model_dump_json() == before


def test_static_membership_work_consumes_original_invocation_budget(monkeypatch):
    monkeypatch.setenv("TEST_DATA_AGENT_MAX_BUSINESS_RULE_EVALUATIONS", "2")
    with pytest.raises(GenerationLimitError):
        prepare(spec(), [scenario(fanout_counts=(1, 2, 3))])


def test_preflight_honors_original_deadline():
    clock = [0.0]
    budget = GenerationBudget(max_seconds=1, clock=lambda: clock[0])
    clock[0] = 2.0
    with pytest.raises(GenerationLimitError):
        prepare_relational_scenarios(spec(), (scenario(),), seed=7, budget=budget)


@pytest.mark.parametrize("kind", ["native", "row", "weighted"])
def test_all_known_key_writers_reject_before_execution(kind):
    from test_data_agent.core.constraint import Constraint
    from test_data_agent.rules.models import BusinessRules
    source = spec()
    if kind == "native":
        source.constraints = [Constraint(type="formula", entity="children", fields=["parent_key"],
                                         expression="parent_key + 1", confidence=1)]
    elif kind == "row":
        source.business_rules = BusinessRules(row_rules=[{"type": "formula", "table": "children",
            "field": "parent_key", "expression": "parent_key + 1"}])
    else:
        source.business_rules = BusinessRules(scenarios=[{"name": "fictional", "weight": 1,
            "field_values": {"children": {"parent_key": 1}}}])
    with pytest.raises(RelationalScenarioError, match="conflicts"):
        prepare(source, [scenario(fanout_counts=(1, 2, 3))])


def test_orphans_cannot_silently_disable_an_explicit_foreign_key_business_check():
    from test_data_agent.rules.models import BusinessRules
    source = spec(mode="mixed")
    source.business_rules = BusinessRules(cross_table_rules=[{"type": "foreign_key",
        "parent_table": "parents", "parent_field": "key", "child_table": "children", "child_field": "parent_key"}])
    with pytest.raises(RelationalScenarioError, match="foreign-key business check"):
        prepare(source, [scenario(orphan_count=1)])


def test_mismatched_key_types_fail_before_allocation():
    source = spec()
    source.entities[1].fields[0].data_type = "string"
    with pytest.raises(RelationalScenarioError, match="matching integer or string"):
        prepare(source, [scenario()])


def test_declaration_count_is_bounded_before_edge_iteration():
    with pytest.raises(RelationalScenarioError, match="count exceeds"):
        prepare(spec(), [scenario()] * 1001)
