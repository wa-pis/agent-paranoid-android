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


@pytest.mark.parametrize("fault", [None, "source", "traversal", "symlink", "missing"])
def test_configured_query_references_use_owned_files_and_environment(tmp_path, monkeypatch, fault):
    from test_data_agent.io.transformation_query_workflow import (
        _ConfiguredQueryReference, _temporary_configured_query_profile,
    )
    from test_data_agent.mcp_transformation_candidate import _configured_query_tools
    monkeypatch.setenv("TEST_DATA_AGENT_WORKSPACE_ROOT", str(tmp_path))
    profile, bindings, captures = fixture(tmp_path, SqlQueryAdapter.POSTGRES)
    config = next(iter(bindings.values())).config
    monkeypatch.setattr(PostgresConfig, "from_env", classmethod(lambda cls: config))
    query = tmp_path / "input.sql"
    query.write_text("SELECT status FROM public.orders")
    refs = {key: _ConfiguredQueryReference(SqlQueryAdapter.POSTGRES, "warehouse",
        binding.request.entity, "input.sql", binding.max_rows, binding.max_bytes,
        binding.max_seconds) for key, binding in bindings.items()}
    key = next(iter(refs))
    if fault == "source":
        refs[key] = replace(refs[key], source_id="other")
    elif fault == "traversal":
        refs[key] = replace(refs[key], query_file="../input.sql")
    elif fault == "symlink":
        (tmp_path / "link.sql").symlink_to(query)
        refs[key] = replace(refs[key], query_file="link.sql")
    elif fault == "missing":
        refs[key] = replace(refs[key], query_file="missing.sql")
    calls = []
    paths = []

    def capture(binding, *, max_seconds):
        calls.append(binding)
        paths.append(binding.request.query_file)
        assert binding.request.query_file.parent != tmp_path
        assert binding.request.query_file.read_text() == query.read_text()
        return captures[binding.request.entity_name]

    monkeypatch.setattr("test_data_agent.io.transformation_postgres_capture._capture_configured_postgres", capture)
    if fault is not None:
        with pytest.raises(TransformationBatchError, match="invalid configured SQL reference"):
            with _temporary_configured_query_profile(tmp_path, profile, references=refs,
                    max_total_bytes=65536, max_review_bytes=32768, budget=GenerationBudget(30)):
                pytest.fail("refused reference entered capture")
        assert calls == []
    else:
        with _configured_query_tools(tmp_path, profile, references=refs,
                max_total_bytes=65536, max_review_bytes=32768) as tool:
            first = tool("review", "batch.yaml", 65536, 32768, 65536)
            second = tool("review", "batch.yaml", 65536, 32768, 65536)
            assert first == second
            assert len(calls) == 2
            assert "alpha" not in str(first)
        from test_data_agent.cli_transformation_candidate import _candidate_configured_query_review
        assert _candidate_configured_query_review(root=tmp_path, profile=profile,
            references=refs, max_total_bytes=65536, max_review_bytes=32768) == 0
        assert len(calls) == 4
        with pytest.raises(TransformationBatchError):
            tool("review", "batch.yaml", 65536, 32768, 65536)
        assert len(calls) == 4
        assert all(not path.exists() for path in paths)
        assert not list(tmp_path.glob("*.query"))


@pytest.mark.parametrize("source_id", ["trino", "unregistered"])
def test_configured_trino_reference_uses_deployment_config(tmp_path, monkeypatch, source_id):
    from contextlib import contextmanager
    from test_data_agent.io import transformation_query_workflow as workflow
    from test_data_agent.trino_config import TrinoConfig
    profile, bindings, _ = fixture(tmp_path, SqlQueryAdapter.TRINO)
    (tmp_path / "query.sql").write_text("SELECT status FROM lake.safe.orders")
    configured = next(iter(bindings.values())).config
    monkeypatch.setattr(TrinoConfig, "from_env", classmethod(lambda cls: configured))
    refs = {key: workflow._ConfiguredQueryReference(SqlQueryAdapter.TRINO, source_id,
        binding.request.entity, "query.sql", 3, 16384, 10.0) for key, binding in bindings.items()}
    seen = []

    @contextmanager
    def capture(root, profile, *, queries, **kwargs):
        seen.extend(queries.values())
        assert all(binding.config is configured for binding in queries.values())
        yield root, None

    monkeypatch.setattr(workflow, "_temporary_query_batch_profile", capture)
    if source_id == "trino":
        with workflow._temporary_configured_query_profile(tmp_path, profile, references=refs,
                max_total_bytes=65536, max_review_bytes=32768, budget=GenerationBudget(30)):
            assert len(seen) == 2
    else:
        with pytest.raises(TransformationBatchError, match="invalid configured SQL reference"):
            with workflow._temporary_configured_query_profile(tmp_path, profile, references=refs,
                    max_total_bytes=65536, max_review_bytes=32768, budget=GenerationBudget(30)):
                pytest.fail("unknown deployment source entered capture")
        assert not seen


def test_configured_mcp_rejects_parent_workspace_before_capture(tmp_path, monkeypatch):
    from test_data_agent.mcp_transformation_candidate import _configured_query_tools
    from test_data_agent.mcp_generator_server import WorkspacePathError
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    monkeypatch.setenv("TEST_DATA_AGENT_WORKSPACE_ROOT", str(workspace))
    profile, _, _ = fixture(tmp_path, SqlQueryAdapter.POSTGRES)
    calls = []
    monkeypatch.setattr(PostgresConfig, "from_env", classmethod(lambda cls: calls.append(True)))
    with pytest.raises(WorkspacePathError):
        with _configured_query_tools(tmp_path, profile, references={},
                max_total_bytes=65536, max_review_bytes=32768):
            pytest.fail("outside workspace admitted")
    assert not calls


@pytest.mark.parametrize("output_format", ["csv", "parquet", "postgresql_sql"])
def test_configured_cli_retains_selected_output_and_expires_capture(tmp_path, monkeypatch, capsys, output_format):
    from test_data_agent.io.transformation_query_workflow import _ConfiguredQueryReference
    from test_data_agent.core.transformation_policy import BehaviorPolicy
    profile, bindings, captures = fixture(tmp_path, SqlQueryAdapter.POSTGRES)
    config = next(iter(bindings.values())).config
    monkeypatch.setattr(PostgresConfig, "from_env", classmethod(lambda cls: config))
    (tmp_path / "input.sql").write_text("SELECT status FROM public.orders")
    refs = {key: _ConfiguredQueryReference(SqlQueryAdapter.POSTGRES, "warehouse",
        binding.request.entity, "input.sql", 3, 16384, 10.0) for key, binding in bindings.items()}
    if output_format != "csv":
        for item in profile.inputs:
            path = tmp_path / item.policy
            raw = yaml.safe_load(path.read_bytes())
            raw["output"] = {"format": output_format, "fields": [
                {"name": "label", "type": "string"}, {"name": "measured", "type": "integer"}]}
            if output_format == "postgresql_sql":
                raw["output"]["table"] = "summary"
            policy = BehaviorPolicy.model_validate(raw)
            path.write_bytes(dump_behavior_policy_yaml(policy, max_bytes=65536, budget=GenerationBudget(5)))
    paths = []
    calls = []

    def capture(binding, *, max_seconds):
        calls.append(binding)
        paths.append(binding.request.query_file)
        return captures[binding.request.entity_name]

    monkeypatch.setattr("test_data_agent.io.transformation_postgres_capture._capture_configured_postgres", capture)
    monkeypatch.setattr("test_data_agent.io.transformation_batch_receipt.issue_batch_receipt",
        lambda *a, **k: pytest.fail("substitution does not require approval"))
    from test_data_agent.cli_transformation_candidate import _candidate_common_main
    (tmp_path / "profile.yaml").write_text(yaml.safe_dump(profile.model_dump(mode="json", exclude_unset=True)))
    (tmp_path / "references.yaml").write_text(yaml.safe_dump({"schema_version": "0.1", "queries": {
        key: {"adapter": reference.adapter.value, "source_id": reference.source_id,
            "entity": reference.entity, "query_file": reference.query_file,
            "max_rows": reference.max_rows, "max_bytes": reference.max_bytes,
            "max_seconds": reference.max_seconds} for key, reference in refs.items()}}))
    assert _candidate_common_main(["query-execute", str(tmp_path), "profile.yaml", "references.yaml",
        "selected", "--max-total-input-bytes", "65536", "--max-review-bytes", "32768",
        "--max-output-bytes", "65536"]) == 0
    assert len(calls) == 2 and all(not path.exists() for path in paths)
    suffix = {"csv": "csv", "parquet": "parquet", "postgresql_sql": "sql"}[output_format]
    outputs = list((tmp_path / "selected").glob(f"*.{suffix}"))
    assert len(outputs) == 2
    if output_format == "parquet":
        assert pq.read_table(outputs[0]).to_pylist() == [{"label": "gamma", "measured": 8}, {"label": "delta", "measured": 7}]
    else:
        assert "gamma" in outputs[0].read_text()
        assert "alpha" not in outputs[0].read_text()
    assert "alpha" not in capsys.readouterr().out
    assert not list(tmp_path.glob("*.query"))


@pytest.mark.parametrize("fault", ["existing", "traversal", "symlink", "output_limit"])
def test_configured_cli_destination_and_output_limits_refuse_before_capture(tmp_path, monkeypatch, fault):
    from test_data_agent.cli_transformation_candidate import _candidate_configured_query_execute
    from test_data_agent.core.transformation_limits import TransformationLimitError
    profile, _, _ = fixture(tmp_path, SqlQueryAdapter.POSTGRES)
    calls = []
    monkeypatch.setattr(PostgresConfig, "from_env", classmethod(lambda cls: calls.append(True)))
    destination = "selected"
    cap = 65536
    if fault == "existing":
        (tmp_path / destination).mkdir()
    elif fault == "traversal":
        destination = "../selected"
    elif fault == "symlink":
        (tmp_path / destination).symlink_to(tmp_path / "missing")
    else:
        monkeypatch.setenv("TEST_DATA_AGENT_MAX_OUTPUT_BYTES", "1024")
    with pytest.raises((ValueError, TransformationLimitError)):
        _candidate_configured_query_execute(root=tmp_path, profile=profile, references={},
            destination=destination, max_total_bytes=65536, max_review_bytes=32768,
            max_output_bytes=cap)
    assert not calls


@pytest.mark.parametrize("approve", [False, True])
def test_configured_cli_preservation_uses_existing_tty_receipt(tmp_path, monkeypatch, approve):
    from test_data_agent.cli_transformation_candidate import _candidate_configured_query_execute
    from test_data_agent.io.transformation_query_workflow import _ConfiguredQueryReference
    from test_data_agent.core.transformation_policy import BehaviorPolicy
    from test_data_agent.io.transformation_receipt import LocalReceiptError
    profile, bindings, captures = fixture(tmp_path, SqlQueryAdapter.POSTGRES)
    config = next(iter(bindings.values())).config
    monkeypatch.setattr(PostgresConfig, "from_env", classmethod(lambda cls: config))
    (tmp_path / "input.sql").write_text("SELECT status FROM public.orders")
    refs = {key: _ConfiguredQueryReference(SqlQueryAdapter.POSTGRES, "warehouse",
        binding.request.entity, "input.sql", 3, 16384, 10.0) for key, binding in bindings.items()}
    path = tmp_path / profile.inputs[0].policy
    raw = yaml.safe_load(path.read_bytes())
    raw["fields"][0]["behavior"] = {"action": "preserve", "authorization_ref": "local", "comment": "Fictional local review"}
    policy = BehaviorPolicy.model_validate(raw)
    path.write_bytes(dump_behavior_policy_yaml(policy, max_bytes=65536, budget=GenerationBudget(5)))
    paths, approvals = [], []

    def capture(binding, *, max_seconds):
        paths.append(binding.request.query_file)
        return captures[binding.request.entity_name]

    def refusal(batch, receipt, **kwargs):
        approvals.append(batch.snapshot_sha256)
        paths.append(receipt)
        raise LocalReceiptError("local batch confirmation failed")

    monkeypatch.setattr("test_data_agent.io.transformation_postgres_capture._capture_configured_postgres", capture)
    if approve:
        import os
        from test_data_agent.io import transformation_batch_receipt as issuer
        original_open = os.open
        tty = tmp_path / "fictional-tty"
        tty.write_bytes(b"")
        def open_tty(path, flags, *args, **kwargs):
            return original_open(tty if path == "/dev/tty" else path, flags, *args, **kwargs)
        def confirmed(fd, review, digest):
            assert fd >= 0 and digest == __import__("json").loads(review)["snapshot_sha256"]
            approvals.append(digest)
        monkeypatch.setattr(os, "open", open_tty)
        monkeypatch.setattr(issuer, "_confirm_tty_fd", confirmed)
        assert _candidate_configured_query_execute(root=tmp_path, profile=profile, references=refs,
            destination="selected", max_total_bytes=65536, max_review_bytes=32768,
            max_output_bytes=65536) == 0
        assert "alpha" in (tmp_path / "selected" / "input-0.csv").read_text()
        assert not list((tmp_path / "selected").glob("*receipt*"))
    else:
        monkeypatch.setattr("test_data_agent.io.transformation_batch_receipt.issue_batch_receipt", refusal)
        monkeypatch.setattr("test_data_agent.io.transformation_batch._publish_retained_test_batch",
            lambda *a, **k: pytest.fail("refused approval must not publish"))
        with pytest.raises(LocalReceiptError):
            _candidate_configured_query_execute(root=tmp_path, profile=profile, references=refs,
                destination="selected", max_total_bytes=65536, max_review_bytes=32768,
                max_output_bytes=65536)
        assert not (tmp_path / "selected").exists()
    assert len(approvals) == 1
    assert all(not path.exists() for path in paths)


def test_configured_cli_unknown_arguments_and_reference_secrets_are_redacted(tmp_path, capsys):
    from test_data_agent.cli_transformation_candidate import _candidate_common_main
    canary = "fictional-secret-should-not-reflect"
    with pytest.raises(SystemExit):
        _candidate_common_main(["query-execute", "--unknown=" + canary])
    assert canary not in capsys.readouterr().err


def test_configured_cli_reference_config_is_refused_without_reflecting_values(tmp_path, monkeypatch, capsys):
    from test_data_agent.cli_transformation_candidate import _candidate_common_main
    profile, _, _ = fixture(tmp_path, SqlQueryAdapter.POSTGRES)
    (tmp_path / "profile.yaml").write_text(yaml.safe_dump(profile.model_dump(mode="json", exclude_unset=True)))
    canary = "fictional-secret-should-not-reflect"
    (tmp_path / "references.yaml").write_text(yaml.safe_dump({"schema_version": "0.1", "queries": {
        "capture0.query": {"adapter": "postgres", "source_id": "warehouse", "entity": "summary0",
            "query_file": "input.sql", "max_rows": 3, "max_bytes": 16384, "max_seconds": 10.0,
            "password": canary}}}))
    calls = []
    monkeypatch.setattr(PostgresConfig, "from_env", classmethod(lambda cls: calls.append(True)))
    assert _candidate_common_main(["query-execute", str(tmp_path), "profile.yaml", "references.yaml",
        "selected", "--max-total-input-bytes", "65536", "--max-review-bytes", "32768",
        "--max-output-bytes", "65536"]) != 0
    output = capsys.readouterr()
    assert canary not in output.out + output.err
    assert not calls and not (tmp_path / "selected").exists()



def test_configured_cli_refuses_destination_created_during_capture(tmp_path, monkeypatch):
    from test_data_agent.cli_transformation_candidate import _candidate_configured_query_execute
    from test_data_agent.io.transformation_query_workflow import _ConfiguredQueryReference
    profile, bindings, captures = fixture(tmp_path, SqlQueryAdapter.POSTGRES)
    config = next(iter(bindings.values())).config
    monkeypatch.setattr(PostgresConfig, "from_env", classmethod(lambda cls: config))
    (tmp_path / "input.sql").write_text("SELECT status FROM public.orders")
    refs = {key: _ConfiguredQueryReference(SqlQueryAdapter.POSTGRES, "warehouse",
        binding.request.entity, "input.sql", 3, 16384, 10.0) for key, binding in bindings.items()}
    paths = []
    def capture(binding, *, max_seconds):
        paths.append(binding.request.query_file)
        (tmp_path / "selected").mkdir(exist_ok=True)
        return captures[binding.request.entity_name]
    monkeypatch.setattr("test_data_agent.io.transformation_postgres_capture._capture_configured_postgres", capture)
    with pytest.raises(ValueError, match="configured SQL destination changed"):
        _candidate_configured_query_execute(root=tmp_path, profile=profile, references=refs,
            destination="selected", max_total_bytes=65536, max_review_bytes=32768,
            max_output_bytes=65536)
    assert not list((tmp_path / "selected").iterdir())
    assert all(not path.exists() for path in paths)
