"""Synthetic regressions for source hashing and pre-allocation inventory limits."""
from contextlib import contextmanager
from dataclasses import replace
import hashlib
from pathlib import Path
from types import SimpleNamespace

import pytest

from test_data_agent import agent_planning
from test_data_agent.agent_contracts import AgentRequest, AgentSourceType
from test_data_agent.core import limits
from test_data_agent.profiling.budget import (
    LocalProfileBudget, LocalProfileLimitError, LocalProfileLimits, bounded_csv_paths,
)
from test_data_agent.profiling.cache import csv_folder_fingerprint
from test_data_agent import trino_work_budget


def request(path: Path, *, folder: bool = False) -> AgentRequest:
    return AgentRequest(source_type=AgentSourceType.CSV_FOLDER if folder else AgentSourceType.CSV,
                        source_path=path, workspace=path.parent / "workspace")


@pytest.mark.parametrize("folder", [False, True])
def test_fingerprint_preserves_existing_framing(tmp_path, folder):
    path = tmp_path / "fictional.csv"
    payload = b"id\n1\n"
    path.write_bytes(payload)
    digest = hashlib.sha256(b"agent-source-v1\0")
    name = path.name.encode()
    for piece in (len(name).to_bytes(8, "big"), name, len(payload).to_bytes(8, "big"),
                  payload, bytes(8)):
        digest.update(piece)
    assert agent_planning.agent_source_fingerprint(request(tmp_path if folder else path, folder=folder)) == digest.hexdigest()


@pytest.mark.parametrize("file_limit,total_limit,folder", [(8, 100, False), (100, 10, True)])
def test_fingerprint_charges_growth_after_stat(tmp_path, monkeypatch, file_limit, total_limit, folder):
    paths = [tmp_path / "a.csv", tmp_path / "b.csv"] if folder else [tmp_path / "a.csv"]
    for path in paths:
        path.write_bytes(b"x")
    monkeypatch.setenv(limits.MAX_INPUT_FILE_BYTES_ENV, str(file_limit))
    monkeypatch.setenv(limits.MAX_TOTAL_INPUT_BYTES_ENV, str(total_limit))
    original = agent_planning.open_regular_file
    reads = []

    @contextmanager
    def growing(path):
        # Producer growth happens after all preflight statistics, before reading.
        with path.open("ab") as writer:
            writer.write(b"x" * 6 if folder else b"x" * 20)
        with original(path) as handle:
            class Reader:
                def read(self, size):
                    reads.append(size)
                    return handle.read(size)
            yield Reader()

    monkeypatch.setattr(agent_planning, "open_regular_file", growing)
    with pytest.raises(limits.InputLimitError, match="fingerprint input byte limit"):
        agent_planning.agent_source_fingerprint(request(tmp_path if folder else paths[0], folder=folder))
    assert max(reads) <= min(file_limit, total_limit) + 1


@pytest.mark.parametrize("inherited", [False, True])
def test_fingerprint_checks_deadline_after_read(tmp_path, monkeypatch, inherited):
    path = tmp_path / "a.csv"
    path.write_bytes(b"id\n1\n")
    now = [0.0]
    local = LocalProfileBudget(LocalProfileLimits(max_seconds=1), clock=lambda: now[0])
    token = None
    if inherited:
        captured = trino_work_budget.QueryWorkBudget(
            replace(trino_work_budget.DEFAULT_QUERY_WORK_LIMITS, max_invocation_seconds=1),
            monotonic_clock=lambda: now[0],
        )
        token = trino_work_budget._CURRENT_QUERY_WORK_BUDGET.set(captured)
        local = LocalProfileBudget(LocalProfileLimits(max_seconds=100), clock=lambda: now[0])
    monkeypatch.setattr(agent_planning, "LocalProfileBudget", lambda: local)
    original = agent_planning.open_regular_file

    @contextmanager
    def delayed(path):
        with original(path) as handle:
            class Reader:
                def read(self, size):
                    value = handle.read(size)
                    now[0] = 2.0
                    return value
            yield Reader()
    monkeypatch.setattr(agent_planning, "open_regular_file", delayed)
    try:
        error = trino_work_budget.QueryWorkBudgetExceeded if inherited else LocalProfileLimitError
        with pytest.raises(error):
            agent_planning.agent_source_fingerprint(request(path))
    finally:
        if token is not None:
            trino_work_budget._CURRENT_QUERY_WORK_BUDGET.reset(token)


@pytest.mark.parametrize("consumer", [limits.enforce_input_files, LocalProfileBudget().check_input_files])
def test_count_rejection_stops_iterable_before_stat(monkeypatch, consumer):
    monkeypatch.setenv(limits.MAX_INPUT_FILES_ENV, "2")
    visited = []
    def paths():
        for index in range(1000):
            visited.append(index)
            yield Path(f"nonexistent-{index}.csv")
    with pytest.raises(limits.InputLimitError, match="more than 2 files"):
        consumer(paths())
    assert visited == [0, 1, 2]


@pytest.mark.parametrize("consumer", ["inventory", "cache", "agent", "dataset", "detect", "profile", "schema", "rows"])
def test_directory_scan_stops_and_closes_at_limit(tmp_path, monkeypatch, consumer):
    monkeypatch.setenv(limits.MAX_INPUT_FILES_ENV, "2")
    visited = []
    closed = []
    @contextmanager
    def scan(folder):
        def entries():
            for index in range(1000):
                visited.append(index)
                yield SimpleNamespace(name=f"fictional-{index}.csv")
        try:
            yield entries()
        finally:
            closed.append(True)
    monkeypatch.setattr(limits.os, "scandir", scan)
    def forbidden(*args, **kwargs):
        raise AssertionError("eager pathlib enumeration")
    monkeypatch.setattr(Path, "glob", forbidden)
    monkeypatch.setattr(Path, "iterdir", forbidden)
    from test_data_agent.io.readers import load_dataset_rows
    from test_data_agent.profiling import profile_example_folder, profile_schema, load_csv_folder
    calls = {
        "inventory": lambda: bounded_csv_paths(tmp_path, LocalProfileBudget()),
        "cache": lambda: csv_folder_fingerprint(tmp_path),
        "agent": lambda: agent_planning.agent_source_fingerprint(request(tmp_path, folder=True)),
        "dataset": lambda: load_dataset_rows(tmp_path),
        "detect": lambda: agent_planning.detect_agent_source_type(tmp_path),
        "profile": lambda: profile_example_folder(tmp_path),
        "schema": lambda: profile_schema(tmp_path),
        "rows": lambda: load_csv_folder(tmp_path),
    }
    with pytest.raises(limits.InputLimitError, match="more than 2 files"):
        calls[consumer]()
    assert visited == [0, 1, 2]
    assert closed == [True]


def test_inventory_checks_time_for_nonmatching_entries(tmp_path, monkeypatch):
    now = [0.0]
    budget = LocalProfileBudget(LocalProfileLimits(max_seconds=1), clock=lambda: now[0])
    closed = []
    @contextmanager
    def scan(folder):
        def entries():
            now[0] = 2.0
            yield SimpleNamespace(name="ignored.txt")
            raise AssertionError("deadline must stop enumeration")
        try:
            yield entries()
        finally:
            closed.append(True)
    monkeypatch.setattr(limits.os, "scandir", scan)
    with pytest.raises(LocalProfileLimitError):
        bounded_csv_paths(tmp_path, budget)
    assert closed == [True]


def test_inventory_order_and_invalid_entries(tmp_path):
    for name in ["z.csv", "a.csv", "ignored.txt"]:
        (tmp_path / name).write_text("id\n1\n")
    assert [p.name for p in bounded_csv_paths(tmp_path, LocalProfileBudget())] == ["a.csv", "z.csv"]
    (tmp_path / "directory.csv").mkdir()
    with pytest.raises(limits.InputLimitError, match="regular file"):
        csv_folder_fingerprint(tmp_path)


def test_cache_inventory_reuses_explicit_deadline(tmp_path):
    now = [0.0]
    budget = LocalProfileBudget(LocalProfileLimits(max_seconds=1), clock=lambda: now[0])
    now[0] = 2.0
    with pytest.raises(LocalProfileLimitError):
        csv_folder_fingerprint(tmp_path, budget=budget)
