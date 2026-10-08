"""Fictional exact-null and shared-deadline regressions; no live services."""

import pytest
import yaml

from test_data_agent.core.limits import GenerationBudget, GenerationLimitError
from test_data_agent.core.dataset import DatasetSpec
from test_data_agent.core.transformation_policy import BehaviorPolicy, transformation_schema_fingerprint
from test_data_agent.core.transformation_snapshot import SnapshotPart
from test_data_agent.io.transformation_batch import TransformationBatchError, execute_batch, prepare_batch
from test_data_agent.io.transformation_source import _profile_transformation_source, prepare_csv_review_request
from test_data_agent.mcp_transformation_candidate import _common_batch_tool, _mcp_transformation_budget
from test_data_agent.trino_work_budget import (
    DEFAULT_QUERY_WORK_LIMITS, QueryWorkBudget, QueryWorkBudgetExceeded,
    QueryWorkDimension, with_query_work_budget,
)
from test_data_agent.validation.relationship_validator import validate_relationships
from tests.test_transformation_batch import save_fictional_batch_profile


@pytest.mark.parametrize("operation", ["review", "validate", "execute"])
@pytest.mark.parametrize("retained", [False, True])
def test_common_mcp_expiry_during_capture_is_typed_and_never_publishes(tmp_path, operation, retained):
    if operation != "execute" and retained:
        pytest.skip("only execute accepts a destination")
    save_fictional_batch_profile(tmp_path)
    plain = _common_batch_tool(tmp_path)
    reviewed = plain("review", "batch.yaml", 32768, 8192, 8192)
    before = {p.name: p.read_bytes() for p in tmp_path.iterdir()}
    ticks = iter([0.0] * 5)
    request_budget = QueryWorkBudget(DEFAULT_QUERY_WORK_LIMITS,
        monotonic_clock=lambda: next(ticks, 1000.0))
    tool = with_query_work_budget(plain, DEFAULT_QUERY_WORK_LIMITS,
        budget_provider=lambda: request_budget)
    with pytest.raises(QueryWorkBudgetExceeded) as caught:
        tool(operation, "batch.yaml", 32768, 8192, 8192,
            reviewed["snapshot_sha256"], destination="output" if retained else None)
    assert caught.value.dimension is QueryWorkDimension.INVOCATION_SECONDS
    assert {p.name: p.read_bytes() for p in tmp_path.iterdir()} == before


def test_common_mcp_expiry_before_retained_rename_cleans_staging(tmp_path, monkeypatch):
    from test_data_agent.io import transformation_publish

    save_fictional_batch_profile(tmp_path)
    plain = _common_batch_tool(tmp_path)
    reviewed = plain("review", "batch.yaml", 32768, 8192, 8192)
    before = {p.name: p.read_bytes() for p in tmp_path.iterdir()}
    clock = [0.0]
    budget = QueryWorkBudget(DEFAULT_QUERY_WORK_LIMITS, monotonic_clock=lambda: clock[0])
    original_write = transformation_publish.atomic_write_bytes

    def write_then_expire(path, payload):
        original_write(path, payload)
        if path.parent.parent == tmp_path:
            clock[0] = 1000.0

    monkeypatch.setattr(transformation_publish, "atomic_write_bytes", write_then_expire)
    tool = with_query_work_budget(plain, DEFAULT_QUERY_WORK_LIMITS, budget_provider=lambda: budget)
    with pytest.raises(QueryWorkBudgetExceeded):
        tool("execute", "batch.yaml", 32768, 8192, 8192,
             reviewed["snapshot_sha256"], destination="output")
    assert {p.name: p.read_bytes() for p in tmp_path.iterdir()} == before


def test_mcp_budget_retains_generation_deadline_and_cleanup_warning():
    from test_data_agent.io.transformation_publish import TransformationCleanupError

    with pytest.raises(GenerationLimitError):
        with _mcp_transformation_budget() as budget:
            budget.max_seconds = 1e-20
            budget.check("fictional work")
    with pytest.raises(TransformationCleanupError, match="cleanup incomplete"):
        with _mcp_transformation_budget() as budget:
            budget.max_seconds = 1e-20
            raise TransformationCleanupError("cleanup incomplete")


@pytest.mark.parametrize("child_values,parent_empty,one_to_one,valid", [
    (["old-c"], False, False, False),
    (["old-c"], True, False, True),
    (["old-c", "old-c"], True, True, False),
])
def test_batch_relationships_distinguish_empty_text_from_null(child_values, parent_empty, one_to_one, valid):
    requests = []
    for entity, values in (("parents", ["old-a", "old-c"] if parent_empty else ["old-a"]),
                           ("children", child_values)):
        source = SnapshotPart("source", entity,
            ("key\n" + "".join(("NULL" if value is None else value) + "\n" for value in values)).encode())
        data = {"schema_version": "0.1", "seed": 7, "schema_fingerprint": "0" * 64,
            "csv_nulls": {"input_token": "NULL", "output_token": "NULL"},
            "domains": [{"name": "shared", "mapping": {"kind": "inline", "entries": [
                {"original": ["old-a"], "replacement": ["new-a"]},
                {"original": ["old-c"], "replacement": [""]},
                {"original": [None], "replacement": [None]}]}}],
            "fields": [{"entity": entity, "field": "key", "sensitivity": "non_sensitive",
                "behavior": {"action": "substitute", "mapping": {"kind": "domain", "name": "shared"}}}]}
        if None not in values:
            data["domains"][0]["mapping"]["entries"].pop()
        policy = BehaviorPolicy.model_validate(data)
        profile = _profile_transformation_source(source, policy, max_bytes=8192, budget=GenerationBudget(5))
        data["schema_fingerprint"] = transformation_schema_fingerprint(profile)
        requests.append(prepare_csv_review_request(yaml.safe_dump(BehaviorPolicy.model_validate(data).model_dump(mode="json")).encode(), source, (),
            max_total_bytes=32768, max_review_bytes=8192, budget=GenerationBudget(5)))
    spec_data = {"schema_version": "1.1", "entities": [
        {"name": entity, "row_count": len(values), "fields": [
            {"name": "key", "data_type": "string", "nullable": True}]}
        for entity, values in (("parents", ["a", "b"] if parent_empty else ["a"]),
                               ("children", child_values))],
        "relationships": [{"parent_entity": "parents", "parent_field": "key",
            "child_entity": "children", "child_field": "key", "confidence": 1,
            "relationship_type": "one_to_one" if one_to_one else "many_to_one"}]}
    spec = DatasetSpec.model_validate(spec_data)
    batch = prepare_batch(tuple(requests), yaml.safe_dump(spec_data).encode(),
        max_total_bytes=32768, max_review_bytes=8192, budget=GenerationBudget(5))
    arguments = dict(expected_snapshot_sha256=batch.snapshot_sha256, max_total_bytes=32768,
        max_review_bytes=8192, max_output_bytes=8192, budget=GenerationBudget(5))
    if valid:
        assert execute_batch(batch, **arguments)[1].rows == tuple(
            (None if value is None else "",) for value in child_values)
    else:
        with pytest.raises(TransformationBatchError):
            execute_batch(batch, **arguments)
    # Source-free validation retains its historical CSV empty-null behavior.
    rows = {"parents": [{"key": "new-a"}], "children": [{"key": ""}, {"key": ""}]}
    assert not validate_relationships(rows, spec)
    assert validate_relationships(rows, spec, empty_string_is_null=False)
    rows["children"] = [{"key": None}]
    assert not validate_relationships(rows, spec, empty_string_is_null=False)


@pytest.mark.parametrize("operation", ["review", "execute"])
def test_single_mcp_expiry_during_work_is_typed(tmp_path, monkeypatch, operation):
    from test_data_agent.mcp_generator_server import review_transformation
    from test_data_agent.mcp_transformation_candidate import _execute_candidate_transformation

    save_fictional_batch_profile(tmp_path)
    monkeypatch.setenv("TEST_DATA_AGENT_WORKSPACE_ROOT", str(tmp_path))
    profile = yaml.safe_load((tmp_path / "batch.yaml").read_bytes())["inputs"][0]
    reviewed = review_transformation(profile["source"], profile["policy"], profile["entity"])
    before = {p.name: p.read_bytes() for p in tmp_path.iterdir()}
    ticks = iter([0.0] * 5)
    request_budget = QueryWorkBudget(DEFAULT_QUERY_WORK_LIMITS,
        monotonic_clock=lambda: next(ticks, 1000.0))
    target = review_transformation if operation == "review" else _execute_candidate_transformation
    tool = with_query_work_budget(target, DEFAULT_QUERY_WORK_LIMITS,
        budget_provider=lambda: request_budget)
    arguments = dict(input_path=profile["source"], policy_path=profile["policy"],
        table_name=profile["entity"])
    if operation == "execute":
        arguments.update(output_path="output", snapshot_sha256=reviewed["snapshot_sha256"])
    with pytest.raises(QueryWorkBudgetExceeded) as caught:
        tool(**arguments)
    assert caught.value.dimension is QueryWorkDimension.INVOCATION_SECONDS
    assert {p.name: p.read_bytes() for p in tmp_path.iterdir()} == before


def test_expiry_during_retained_publish_removes_destination(tmp_path, monkeypatch):
    from test_data_agent.io import transformation_publish

    save_fictional_batch_profile(tmp_path)
    plain = _common_batch_tool(tmp_path)
    reviewed = plain("review", "batch.yaml", 32768, 8192, 8192)
    before = {p.name: p.read_bytes() for p in tmp_path.iterdir()}
    clock = [0.0]
    budget = QueryWorkBudget(DEFAULT_QUERY_WORK_LIMITS, monotonic_clock=lambda: clock[0])
    original_publish = transformation_publish.publish_directory

    def publish_then_expire(staging, destination):
        original_publish(staging, destination)
        clock[0] = 1000.0

    monkeypatch.setattr(transformation_publish, "publish_directory", publish_then_expire)
    tool = with_query_work_budget(plain, DEFAULT_QUERY_WORK_LIMITS, budget_provider=lambda: budget)
    with pytest.raises(QueryWorkBudgetExceeded):
        tool("execute", "batch.yaml", 32768, 8192, 8192,
            reviewed["snapshot_sha256"], destination="output")
    assert {p.name: p.read_bytes() for p in tmp_path.iterdir()} == before
