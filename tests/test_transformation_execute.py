"""Fictional inputs only: closed executor, no public interface or file output."""

import csv
import io
from dataclasses import replace
from importlib import import_module

import pytest
import yaml

from test_data_agent.core.limits import GenerationBudget
from test_data_agent.core.transformation_snapshot import SnapshotPart
from test_data_agent.core.transformation_policy import transformation_schema_fingerprint
from test_data_agent.adapters.csv_file import csv_profile_to_dataset_profile
from test_data_agent.csv_profiler import profile_csv_bytes
from test_data_agent.io.transformation_source import prepare_csv_review_request


def request(target="second", complete=True, behavior=None):
    source = SnapshotPart("source", "items", b"flag,code\ntrue,001\nfalse,002\n")
    profile = csv_profile_to_dataset_profile(profile_csv_bytes(
        source.payload, source.name, budget=GenerationBudget(5)))
    def table(path):
        return {"kind": "csv", "path": path, "source_columns": ["old"],
                "replacement_columns": ["new"]}
    policy = yaml.safe_dump({"schema_version": "0.1", "seed": 7,
        "schema_fingerprint": transformation_schema_fingerprint(profile),
        "file_text_mapping": table("all.csv"), "fields": [
            {"entity": "items", "field": "flag", "sensitivity": "non_sensitive",
             "behavior": behavior or {"action": "replace_text"}},
            {"entity": "items", "field": "code", "sensitivity": "non_sensitive",
             "behavior": {"action": "replace_text", "mapping": table("code.csv")}},
        ]}).encode()
    global_pairs = b"old,new\ntrue,no\n001,1\n002,global\nsecond,cascade\n"
    if complete:
        global_pairs += b"false,yes\n"
    column_pairs = io.StringIO(newline="")
    csv.writer(column_pairs).writerows([("old", "new"), ("002", target)])
    return prepare_csv_review_request(policy, source, (
        SnapshotPart("mapping", "all.csv", global_pairs),
        SnapshotPart("mapping", "code.csv", column_pairs.getvalue().encode()),
    ), max_total_bytes=8192, max_review_bytes=4096, budget=GenerationBudget(5))


def execute(material, limit=8192):
    module = import_module("test_data_agent.io.transformation_execute")
    return module.replace_csv_snapshot(material, max_total_bytes=8192,
        max_review_bytes=4096, max_output_bytes=limit, budget=GenerationBudget(5))


def test_closed_csv_exact_text_override_no_cascade():
    assert list(csv.reader(io.StringIO(execute(request()).decode()))) == [
        ["flag", "code"], ["no", "1"], ["yes", "second"]]


@pytest.mark.parametrize("case", ["unmatched", "tampered", "budget", "pii"])
def test_closed_csv_fails_without_returning_partial_output(case):
    material = request(target="fictional@example.com" if case == "pii" else "second",
                       complete=case != "unmatched")
    if case == "tampered":
        material = replace(material, parts=tuple(
            replace(part, payload=b"flag,code\ntrue,001\n")
            if part.kind == "source" else part for part in material.parts))
    module = import_module("test_data_agent.io.transformation_execute")
    with pytest.raises(module.TransformationExecutionError) as caught:
        execute(material, 1 if case == "budget" else 8192)
    assert str(caught.value) == "invalid CSV replacement"
    assert caught.value.__context__ is None


@pytest.mark.parametrize("target", ['quoted,"cell"', "two\nlines", "кириллица", ""])
def test_closed_csv_roundtrips_literal_replacement(target):
    output = execute(request(target=target))
    rows = list(csv.reader(io.StringIO(output.decode(), newline="")))
    assert rows == [["flag", "code"], ["no", "1"], ["yes", target]]
    assert execute(request(target=target), len(output)) == output
    module = import_module("test_data_agent.io.transformation_execute")
    with pytest.raises(module.TransformationExecutionError):
        execute(request(target=target), len(output) - 1)


@pytest.mark.parametrize("behavior", [
    {"action": "preserve", "authorization_ref": "not-approval", "comment": "fictional enum"},
    {"action": "replace_text", "unmatched": {
        "action": "preserve", "authorization_ref": "not-approval", "comment": "fictional enum"}},
])
def test_closed_replace_only_rejects_other_actions_and_preservation(behavior):
    material = request(behavior=behavior)
    module = import_module("test_data_agent.io.transformation_execute")
    with pytest.raises(module.TransformationExecutionError, match="^invalid CSV replacement$"):
        execute(material)


@pytest.mark.parametrize("limit", [0, -1, True, 1.5])
def test_closed_csv_rejects_invalid_output_limits(limit):
    module = import_module("test_data_agent.io.transformation_execute")
    with pytest.raises(module.TransformationExecutionError, match="^invalid CSV replacement$"):
        execute(request(), limit)


def test_closed_csv_enforces_invocation_deadline():
    material = request()
    tick = [0.0]
    budget = GenerationBudget(max_seconds=1, clock=lambda: tick[0])
    tick[0] = 2.0
    module = import_module("test_data_agent.io.transformation_execute")
    with pytest.raises(module.TransformationExecutionError, match="^invalid CSV replacement$"):
        module.replace_csv_snapshot(material, max_total_bytes=8192, max_review_bytes=4096,
                                    max_output_bytes=8192, budget=budget)


def test_closed_csv_drops_selected_column_without_changing_row_order():
    material = request(complete=False, behavior={"action": "drop"})
    assert list(csv.reader(io.StringIO(execute(material).decode()))) == [
        ["code"], ["1"], ["second"]]
