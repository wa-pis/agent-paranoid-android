"""Fictional owned SQL snapshots through the same closed CLI/MCP common consumer."""
import io
from dataclasses import replace

import pytest
import yaml

from test_data_agent.core.limits import GenerationBudget, GenerationLimitError
from test_data_agent.core.transformation_policy import transformation_schema_fingerprint
from test_data_agent.core.transformation_yaml import dump_behavior_policy_yaml
from test_data_agent.io.transformation_batch import TransformationBatchError
from test_data_agent.io.transformation_batch_profile import BatchProfile
from test_data_agent.io.transformation_query_snapshot import _capture_query_result
from test_data_agent.io.transformation_query_workflow import _QueryBatchInput, _temporary_query_batch_profile
from test_data_agent.io.transformation_source import _profile_transformation_source
from test_data_agent.sql_query_source import SqlQueryAdapter
from test_data_agent.postgres_config import PostgresConfig
from tests.test_transformation_query_capture import setup
from tests.test_trino_client import client_config

pa = pytest.importorskip("pyarrow")
pq = pytest.importorskip("pyarrow.parquet")


def fixture(tmp_path, adapter):
    request, kwargs = setup(tmp_path, adapter)
    target = io.BytesIO()
    pq.write_table(pa.Table.from_arrays([pa.array(["alpha", "beta"]), pa.array([2, 1])],
        schema=kwargs["schema"]), target)
    config = (PostgresConfig(source_id="warehouse", host="fictional.invalid", port=5432,
        database="fictional", user="fictional", allowed_schemas=frozenset({"public"}),
        allowed_tables=frozenset({"public.orders"}),
        allowed_columns=frozenset({"public.orders.status"})) if adapter is SqlQueryAdapter.POSTGRES
        else replace(client_config(max_result_rows=4), allowed_catalogs=frozenset({"lake"}),
            allowed_schemas=frozenset({"safe"}),
            allowed_table_columns=frozenset({"lake.safe.orders.*"})))
    inputs, bindings, captures = [], {}, {}
    for index in range(2):
        entity = f"summary{index}"
        current = replace(request, entity=entity)
        source = _capture_query_result(target.getvalue(), adapter=f"{adapter.value}_query",
            query_sha256="a" * 64, entity=current.entity_name)
        policy = kwargs["policy"].model_copy(update={"fields": tuple(
            field.model_copy(update={"entity": current.entity_name}) for field in kwargs["policy"].fields)})
        evidence = _profile_transformation_source(source, policy,
            max_bytes=65536, budget=GenerationBudget(5))
        policy = policy.model_copy(update={"schema_fingerprint": transformation_schema_fingerprint(evidence)})
        policy_path = f"policy{index}.yaml"
        (tmp_path / policy_path).write_bytes(dump_behavior_policy_yaml(policy, max_bytes=65536,
            budget=GenerationBudget(5)))
        path = f"capture{index}.query"
        inputs.append({"entity": current.entity_name, "source": path, "policy": policy_path})
        bindings[path] = _QueryBatchInput(current, config, 3, 16384, 10.0)
        captures[current.entity_name] = source
    (tmp_path / "validation.yaml").write_text(yaml.safe_dump({"schema_version": "1.1", "entities": [
        {"name": f"warehouse.summary{index}", "row_count": 2, "fields": [
            {"name": "label", "data_type": "string"}, {"name": "measured", "data_type": "integer"}]}
        for index in range(2)], "validation_settings": {"validate_schema": False,
        "validate_relationships": False, "validate_constraints": False, "validate_privacy": False}}))
    profile = BatchProfile.model_validate({"schema_version": "0.1", "validation": "validation.yaml", "inputs": inputs})
    return profile, bindings, captures


@pytest.mark.parametrize("adapter", list(SqlQueryAdapter))
def test_captured_queries_use_common_cli_mcp_without_reconnect(tmp_path, monkeypatch, capsys, adapter):
    from test_data_agent.cli_transformation_candidate import _candidate_common_main
    from test_data_agent.mcp_transformation_candidate import _common_batch_tool
    profile, bindings, captures = fixture(tmp_path, adapter)
    calls = []

    def capture(binding, *, max_seconds):
        calls.append(max_seconds)
        return captures[binding.request.entity_name]

    module = ("transformation_postgres_capture" if adapter is SqlQueryAdapter.POSTGRES
              else "transformation_trino_stream")
    name = "_capture_configured_postgres" if adapter is SqlQueryAdapter.POSTGRES else "_capture_configured_trino"
    monkeypatch.setattr(f"test_data_agent.io.{module}.{name}", capture)
    budget = GenerationBudget(30)
    with _temporary_query_batch_profile(tmp_path, profile, queries=bindings,
            max_total_bytes=65536, max_review_bytes=32768, budget=budget) as (root, batch):
        assert root != tmp_path and root.exists()
        tool = _common_batch_tool(root)
        result = tool("review", "batch.yaml", 65536, 32768, 65536)
        assert result["snapshot_sha256"] == batch.snapshot_sha256
        assert "alpha" not in str(result)
        result = tool("validate", "batch.yaml", 65536, 32768, 65536,
            snapshot_sha256=batch.snapshot_sha256)
        assert result["status"] == "closed_validation_completed"
        assert _candidate_common_main(["validate", str(root), "batch.yaml", "--snapshot-sha256",
            batch.snapshot_sha256, "--max-total-input-bytes", "65536", "--max-review-bytes", "32768",
            "--max-output-bytes", "65536"]) == 0
        assert "alpha" not in capsys.readouterr().out
        assert len(calls) == 2
    assert not root.exists()
    assert not list(tmp_path.glob("*.query"))


@pytest.mark.parametrize("fault", ["adapter", "entity", "allocation", "path", "policy_change", "later_bytes", "later_rows", "later_seconds", "shared_limit"])
def test_common_query_preflight_refusals_do_not_materialize(tmp_path, monkeypatch, fault):
    profile, bindings, captures = fixture(tmp_path, SqlQueryAdapter.POSTGRES)
    calls = []

    def capture(binding, *, max_seconds):
        calls.append(binding)
        if fault == "policy_change":
            path = tmp_path / "policy0.yaml"
            path.write_bytes(path.read_bytes() + b"\n")
        return captures[binding.request.entity_name]

    monkeypatch.setattr("test_data_agent.io.transformation_postgres_capture._capture_configured_postgres", capture)
    key = "capture0.query"
    if fault == "adapter":
        bindings[key] = replace(bindings[key], config=client_config())
    if fault == "entity":
        bindings[key] = replace(bindings[key], request=replace(bindings[key].request, entity="other"))
    if fault == "allocation":
        bindings[key] = replace(bindings[key], max_bytes=65537)
    if fault == "later_bytes":
        bindings["capture1.query"] = replace(bindings["capture1.query"], max_bytes=65537)
    if fault == "later_rows":
        bindings["capture1.query"] = replace(bindings["capture1.query"], max_rows=0)
    if fault == "later_seconds":
        bindings["capture1.query"] = replace(bindings["capture1.query"], max_seconds=float("inf"))
    if fault == "shared_limit":
        monkeypatch.setenv("TEST_DATA_AGENT_MAX_TOTAL_INPUT_BYTES", "32768")
    if fault == "path":
        profile.inputs[0].source = "../escape.query"
        bindings["../escape.query"] = bindings.pop(key)
    with pytest.raises((TransformationBatchError, ValueError)):
        with _temporary_query_batch_profile(tmp_path, profile, queries=bindings,
                max_total_bytes=65536, max_review_bytes=32768, budget=GenerationBudget(30)):
            pytest.fail("refusal must not yield a workspace")
    assert len(calls) == (2 if fault == "policy_change" else 0)
    assert not list(tmp_path.glob("*.query"))


def test_remaining_generation_deadline_is_not_reset():
    now = [0.0]
    budget = GenerationBudget(10, clock=lambda: now[0])
    now[0] = 6
    assert budget.remaining_seconds() == 4
    now[0] = 9
    assert budget.remaining_seconds() == 1
    now[0] = 11
    with pytest.raises(GenerationLimitError):
        budget.remaining_seconds()
