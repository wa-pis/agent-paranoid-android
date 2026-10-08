from __future__ import annotations

from dataclasses import replace

import pytest

from test_data_agent import csv_profiler
from test_data_agent.core.dataset import DatasetProfile
from test_data_agent.core.settings import OutputFormat
from test_data_agent.io import workflows
from test_data_agent.trino_work_budget import (
    DEFAULT_QUERY_WORK_LIMITS, QueryWorkBudget, QueryWorkBudgetExceeded,
    generation_budget_for_invocation, with_query_work_budget,
)


def invocation(clock, function):
    limits = replace(DEFAULT_QUERY_WORK_LIMITS, max_invocation_seconds=1.0)
    budget = QueryWorkBudget(limits, monotonic_clock=lambda: clock[0])
    return with_query_work_budget(function, limits, budget_provider=lambda: budget)


@pytest.mark.parametrize("stage", ["row", "finalize", "serialization", "fsync", "directory_fsync"])
def test_registered_csv_profile_honors_deadline_through_publication(tmp_path, monkeypatch, stage):
    from test_data_agent import mcp_generator_server as server
    from test_data_agent.io import path_policy
    clock = [0.0]
    source = tmp_path / "source.csv"
    source.write_text("amount\n1\n2\n")
    monkeypatch.setenv("TEST_DATA_AGENT_WORKSPACE_ROOT", str(tmp_path))
    if stage == "row":
        original = csv_profiler.CSVColumnAccumulator.add
        def expire(self, *args, **kwargs):
            result = original(self, *args, **kwargs)
            clock[0] = 2.0
            return result
        monkeypatch.setattr(csv_profiler.CSVColumnAccumulator, "add", expire)
    elif stage == "finalize":
        original = csv_profiler.CSVColumnAccumulator.to_profile
        def expire(self, *args, **kwargs):
            result = original(self, *args, **kwargs)
            clock[0] = 2.0
            return result
        monkeypatch.setattr(csv_profiler.CSVColumnAccumulator, "to_profile", expire)
    elif stage == "serialization":
        original = DatasetProfile.model_dump_json
        def expire(self, *args, **kwargs):
            result = original(self, *args, **kwargs)
            clock[0] = 2.0
            return result
        monkeypatch.setattr(DatasetProfile, "model_dump_json", expire)
    else:
        original = path_policy.os.fsync
        calls = []
        def expire(descriptor):
            result = original(descriptor)
            calls.append(True)
            if len(calls) >= (2 if stage == "directory_fsync" else 1):
                clock[0] = 2.0
            return result
        monkeypatch.setattr(path_policy.os, "fsync", expire)
    limits = replace(DEFAULT_QUERY_WORK_LIMITS, max_invocation_seconds=1.0)
    budget = QueryWorkBudget(limits, monotonic_clock=lambda: clock[0])
    service = next(tool for tool in server.generator_mcp_services(
        work_limits=limits, budget_provider=lambda: budget) if tool.__name__ == "profile_csv")
    with pytest.raises(QueryWorkBudgetExceeded) as caught:
        service("source.csv", "out/profile.json")
    assert "source.csv" not in str(caught.value)
    assert not (tmp_path / "out/profile.json").exists()
    assert not list(tmp_path.rglob("*.tmp"))


@pytest.mark.parametrize("fsync_number", [1, 2])
def test_expired_profile_publication_keeps_existing_output(tmp_path, monkeypatch, fsync_number):
    from test_data_agent.io import path_policy
    source = tmp_path / "source.csv"
    source.write_text("amount\n1\n")
    output = tmp_path / "profile.json"
    output.write_text("existing")
    clock = [0.0]
    original = path_policy.os.fsync
    calls = []
    def expire(descriptor):
        original(descriptor)
        calls.append(True)
        if len(calls) >= fsync_number:
            clock[0] = 2.0
    monkeypatch.setattr(path_policy.os, "fsync", expire)
    with pytest.raises(QueryWorkBudgetExceeded):
        invocation(clock, lambda: workflows.write_csv_profile_artifact(source, output_path=output))()
    assert output.read_text() == "existing"
    assert not list(tmp_path.glob("*.tmp"))
    assert not list(tmp_path.glob("*.rollback"))


@pytest.mark.parametrize("stage", ["profile", "generation"])
def test_csv_generation_inherits_request_budget(tmp_path, monkeypatch, stage):
    source = tmp_path / "source.csv"
    source.write_text("amount\n1\n2\n")
    output = tmp_path / "out/data.json"
    clock = [0.0]
    generated = []
    if stage == "profile":
        original = csv_profiler.CSVColumnAccumulator.add
        def expire(self, *args, **kwargs):
            original(self, *args, **kwargs)
            clock[0] = 2.0
        monkeypatch.setattr(csv_profiler.CSVColumnAccumulator, "add", expire)
    def generate(*args, **kwargs):
        generated.append(True)
        clock[0] = 2.0
        return {"source": [{"amount": 1}]}
    monkeypatch.setattr(workflows, "generate_dataset", generate)
    def work():
        return workflows.generate_dataset_from_csv_artifacts(
            source, count=1, seed=1, output_path=output, output_format=OutputFormat.JSON)
    with pytest.raises(QueryWorkBudgetExceeded):
        invocation(clock, work)()
    assert bool(generated) is (stage == "generation")
    assert not output.exists()
    assert not list(tmp_path.rglob("generation_manifest.json"))


def test_deadline_during_bundle_commit_rolls_back(tmp_path, monkeypatch):
    staged = tmp_path / "staged"
    staged.mkdir()
    (staged / "data.json").write_text("synthetic")
    (staged / "generation_manifest.json").write_text("synthetic manifest")
    output = tmp_path / "out"
    clock = [0.0]
    original = workflows.replace_path
    def expire(source, destination):
        original(source, destination)
        clock[0] = 2.0
    monkeypatch.setattr(workflows, "replace_path", expire)
    def work():
        workflows.commit_single_entity_bundle(staged, output, primary_output_name="data.json",
                                               budget=generation_budget_for_invocation())
    with pytest.raises(QueryWorkBudgetExceeded):
        invocation(clock, work)()
    assert not output.exists()
    assert (staged / "data.json").exists()
    assert (staged / "generation_manifest.json").exists()


def test_nonexpired_and_unbudgeted_csv_profiles_remain_valid(tmp_path):
    source = tmp_path / "source.csv"
    source.write_text("amount\n1\n2\n")
    output = tmp_path / "profile.json"
    result = invocation([0.0], lambda: workflows.write_csv_profile_artifact(source, output_path=output))()
    assert result.entities[0].row_count == 2
    assert output.exists()
    assert csv_profiler.profile_csv(source).row_count == 2


def test_nonexpired_profile_replaces_existing_output_and_cleans_backup(tmp_path):
    source = tmp_path / "source.csv"
    source.write_text("amount\n1\n")
    output = tmp_path / "profile.json"
    output.write_text("existing")
    invocation([0.0], lambda: workflows.write_csv_profile_artifact(source, output_path=output))()
    assert '"source_type": "csv"' in output.read_text()
    assert not list(tmp_path.glob("*.rollback"))


def test_publication_callback_cannot_overwrite_concurrent_output(tmp_path):
    from test_data_agent.io.path_policy import atomic_binary_writer
    output = tmp_path / "profile.json"
    def changed():
        output.write_text("concurrent")
    with pytest.raises(ValueError, match="changed during publication"):
        with atomic_binary_writer(output, check_publication=changed) as handle:
            handle.write(b"synthetic")
    assert output.read_text() == "concurrent"
    assert not list(tmp_path.glob("*.tmp"))


def test_rollback_name_collision_is_preserved(tmp_path, monkeypatch):
    from test_data_agent.io import path_policy
    source = tmp_path / "source.csv"
    source.write_text("amount\n1\n")
    output = tmp_path / "profile.json"
    output.write_text("existing")
    collision = tmp_path / ".profile.json.fixed.rollback"
    collision.write_text("foreign")
    monkeypatch.setattr(path_policy.secrets, "token_hex", lambda *args: "fixed")
    with pytest.raises(ValueError, match="unsafe filesystem path"):
        invocation([0.0], lambda: workflows.write_csv_profile_artifact(source, output_path=output))()
    assert output.read_text() == "existing"
    assert collision.read_text() == "foreign"
    assert not list(tmp_path.glob("*.tmp"))
