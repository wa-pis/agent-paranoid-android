"""Fictional inputs only: closed executor, no public interface or file output."""

import csv
import io
import os
import pty
import select
from concurrent.futures import ThreadPoolExecutor
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


def request(target="second", complete=True, behavior=None,
            source_bytes=b"flag,code\ntrue,001\nfalse,002\n"):
    source = SnapshotPart("source", "items", source_bytes)
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
        max_review_bytes=4096, max_output_bytes=limit, budget=GenerationBudget(5)).csv_bytes


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


@pytest.mark.parametrize("action", ["preserve", "replace_text", "substitute"])
def test_closed_preservation_requires_exact_local_receipt(tmp_path, action):
    from test_data_agent.io.transformation_receipt import _issue_to_tty_fd

    preserve = {"action": "preserve", "authorization_ref": "fictional-ref",
                "comment": "Reviewed fictional flag"}
    behavior = {"action": action, "unmatched": preserve} if action != "preserve" else preserve
    source_bytes = b"flag,code\ntrue,001\nfalse,002\n"
    if action == "substitute":
        source_bytes = b"flag,code\nready,001\nwaiting,002\n"
        behavior["mapping"] = {"kind": "inline", "entries": [
            {"original": ["ready"], "replacement": ["done"]}]}
    material = request(complete=False, behavior=behavior, source_bytes=source_bytes)
    module = import_module("test_data_agent.io.transformation_execute")
    path = tmp_path / "approval.json"
    kwargs = dict(max_total_bytes=8192, max_review_bytes=4096, max_output_bytes=8192)
    with pytest.raises(module.TransformationExecutionError):
        module.replace_csv_snapshot(material, receipt_path=path, budget=GenerationBudget(5), **kwargs)
    master, slave = pty.openpty()
    try:
        with ThreadPoolExecutor(max_workers=1) as pool:
            issued = pool.submit(_issue_to_tty_fd, material, path, slave, GenerationBudget(5))
            prompt = bytearray()
            while b"Type APPROVE" not in prompt:
                assert select.select([master], [], [], 5)[0]
                prompt.extend(os.read(master, 4096))
            os.write(master, b"APPROVE\n")
            issued.result(timeout=5)
        assert b"second" not in prompt
    finally:
        os.close(master)
        os.close(slave)
    output = module.replace_csv_snapshot(material, receipt_path=path,
                                         budget=GenerationBudget(5), **kwargs)
    expected_flags = {"preserve": ("true", "false"), "replace_text": ("no", "false"),
                      "substitute": ("done", "waiting")}[action]
    assert list(csv.reader(io.StringIO(output.csv_bytes.decode()))) == [
        ["flag", "code"], [expected_flags[0], "1"], [expected_flags[1], "second"]]
    assert output.retention.unchanged_percent == ("50.00" if action == "preserve" else "25.00")
    assert output.retention.compared_cells == 4
    assert "second" not in repr(output)
    changed = request(target="changed", complete=False, behavior=behavior, source_bytes=source_bytes)
    with pytest.raises(module.TransformationExecutionError):
        module.replace_csv_snapshot(changed, receipt_path=path, budget=GenerationBudget(5), **kwargs)
    for kind in ("source", "policy", "evidence", "review"):
        tampered = replace(material, parts=tuple(
            replace(part, payload=part.payload + b" ") if part.kind == kind else part
            for part in material.parts))
        with pytest.raises(module.TransformationExecutionError) as caught:
            module.replace_csv_snapshot(tampered, receipt_path=path,
                                         budget=GenerationBudget(5), **kwargs)
        assert str(caught.value) == "invalid CSV replacement"
        assert caught.value.__context__ is None
    original_receipt = path.read_bytes()
    for mode, payload in ((0o644, original_receipt), (0o600, b"not-json"),
                          (0o600, b'{"version":1,"snapshot_sha256":"wrong"}')):
        path.write_bytes(payload)
        path.chmod(mode)
        with pytest.raises(module.TransformationExecutionError) as caught:
            module.replace_csv_snapshot(material, receipt_path=path,
                                         budget=GenerationBudget(5), **kwargs)
        assert str(caught.value) == "invalid CSV replacement"
        assert caught.value.__context__ is None
    path.write_bytes(original_receipt)
    path.chmod(0o600)
    link = tmp_path / "approval-link.json"
    link.symlink_to(path)
    with pytest.raises(module.TransformationExecutionError):
        module.replace_csv_snapshot(material, receipt_path=link,
                                     budget=GenerationBudget(5), **kwargs)


def test_engine_retention_excludes_dropped_cells():
    module = import_module("test_data_agent.io.transformation_execute")
    result = module.replace_csv_snapshot(request(behavior={"action": "drop"}),
        max_total_bytes=8192, max_review_bytes=4096, max_output_bytes=8192,
        budget=GenerationBudget(5))
    assert result.retention.compared_cells == 2
    assert result.retention.excluded_dropped_cells == 2
    assert result.retention.unchanged_percent == "0.00"


def test_all_dropped_columns_have_no_retention_measurement():
    original = request()
    policy = yaml.safe_load(next(part.payload for part in original.parts if part.kind == "policy"))
    policy.pop("file_text_mapping")
    for decision in policy["fields"]:
        decision["behavior"] = {"action": "drop"}
    source = next(part for part in original.parts if part.kind == "source")
    material = prepare_csv_review_request(yaml.safe_dump(policy).encode(), source, (),
        max_total_bytes=8192, max_review_bytes=4096, budget=GenerationBudget(5))
    module = import_module("test_data_agent.io.transformation_execute")
    result = module.replace_csv_snapshot(material, max_total_bytes=8192,
        max_review_bytes=4096, max_output_bytes=8192, budget=GenerationBudget(5))
    assert list(csv.reader(io.StringIO(result.csv_bytes.decode()))) == [[], [], []]
    assert result.retention.status == "unavailable"
    assert result.retention.unchanged_percent is None
    assert result.retention.compared_cells == 0
    assert result.retention.excluded_dropped_cells == 4


@pytest.mark.parametrize("delimiter", [",", ";", "\t", "|"])
@pytest.mark.parametrize("bom", [b"", b"\xef\xbb\xbf"])
def test_execution_uses_profile_dialect_and_source_column_order(delimiter, bom):
    source = bom + (f"code{delimiter}flag\r\n001{delimiter}true\r\n"
                    f"002{delimiter}false\r\n").encode()
    output = execute(request(source_bytes=source))
    assert list(csv.reader(io.StringIO(output.decode()))) == [
        ["code", "flag"], ["1", "no"], ["second", "yes"]]


@pytest.mark.parametrize("kind", ["inline", "csv"])
@pytest.mark.parametrize("case", ["valid", "unmatched", "pii"])
def test_string_substitute_inline_and_csv_have_same_result(kind, case):
    original = request(source_bytes=b"flag,code\ntrue,alpha\nfalse,beta\n")
    source = next(part for part in original.parts if part.kind == "source")
    policy = yaml.safe_load(next(part.payload for part in original.parts if part.kind == "policy"))
    target = "fictional@example.com" if case == "pii" else "second"
    pairs = [("alpha", "first")]
    if case != "unmatched":
        pairs.append(("beta", target))
    mapping = {"kind": "inline", "entries": [
        {"original": [before], "replacement": [after]} for before, after in pairs]}
    parts = [part for part in original.parts if part.kind == "mapping" and part.name == "all.csv"]
    # A global replace rule must not cover a missing substitute key.
    parts[0] = replace(parts[0], payload=parts[0].payload + b"beta,global-fallback\n")
    if kind == "csv":
        mapping = {"kind": "csv", "path": "pairs.csv", "source_columns": ["old"],
                   "replacement_columns": ["new"]}
        payload = io.StringIO(newline="")
        csv.writer(payload).writerows([("old", "new"), *pairs])
        parts.append(SnapshotPart("mapping", "pairs.csv", payload.getvalue().encode()))
    policy["fields"][1]["behavior"] = {"action": "substitute", "mapping": mapping}
    material = prepare_csv_review_request(yaml.safe_dump(policy).encode(), source, tuple(parts),
        max_total_bytes=8192, max_review_bytes=4096, budget=GenerationBudget(5))
    if case != "valid":
        module = import_module("test_data_agent.io.transformation_execute")
        with pytest.raises(module.TransformationExecutionError) as caught:
            execute(material)
        assert str(caught.value) == "invalid CSV replacement"
        assert caught.value.__context__ is None
        return
    assert list(csv.reader(io.StringIO(execute(material).decode()))) == [
        ["flag", "code"], ["no", "first"], ["yes", "second"]]


@pytest.mark.parametrize("missing", [False, True])
@pytest.mark.parametrize("kind", ["inline", "csv"])
@pytest.mark.parametrize("integer", [False, True])
def test_composite_domain_matches_whole_original_tuple(missing, kind, integer):
    source = SnapshotPart("source", "items", b"region,code\n1,A001\n2,A001\n" if integer
                          else b"region,code\nnorth,alpha\nsouth,alpha\n")
    profile = csv_profile_to_dataset_profile(profile_csv_bytes(
        source.payload, source.name, budget=GenerationBudget(5)))
    entries = [{"original": [1, "A001"], "replacement": [11, "first"]} if integer else
               {"original": ["north", "alpha"], "replacement": ["west", "first"]}]
    if not missing:
        entries.append({"original": [2, "A001"], "replacement": [22, "second"]} if integer else
                       {"original": ["south", "alpha"], "replacement": ["east", "second"]})
    mapping = {"kind": "inline", "entries": entries}
    parts = ()
    if kind == "csv":
        mapping = {"kind": "csv", "path": "pairs.csv", "source_columns": ["old_region", "old_code"],
                   "replacement_columns": ["new_region", "new_code"]}
        payload = io.StringIO(newline="")
        csv.writer(payload).writerows([
            ("old_region", "old_code", "new_region", "new_code"),
            *(tuple(entry["original"] + entry["replacement"]) for entry in entries)])
        parts = (SnapshotPart("mapping", "pairs.csv", payload.getvalue().encode()),)
    policy = yaml.safe_dump({"schema_version": "0.1", "seed": 7,
        "schema_fingerprint": transformation_schema_fingerprint(profile),
        "domains": [{"name": "pair", "mapping": mapping}],
        "fields": [{"entity": "items", "field": name, "sensitivity": "non_sensitive",
                    "behavior": {"action": "substitute", "mapping": {
                        "kind": "domain", "name": "pair", "component": component}}}
                   for component, name in reversed(list(enumerate(("region", "code"))))],
    }).encode()
    material = prepare_csv_review_request(policy, source, parts, max_total_bytes=8192,
        max_review_bytes=4096, budget=GenerationBudget(5))
    if missing:
        module = import_module("test_data_agent.io.transformation_execute")
        with pytest.raises(module.TransformationExecutionError):
            execute(material)
    else:
        assert list(csv.reader(io.StringIO(execute(material).decode()))) == [
            ["region", "code"], ["11" if integer else "west", "first"],
            ["22" if integer else "east", "second"]]


@pytest.mark.parametrize("kind", ["inline", "csv"])
def test_integer_substitute_is_exact_without_float(kind):
    original = request(source_bytes=b"flag,code\ntrue,1\nfalse,2\n")
    source = next(part for part in original.parts if part.kind == "source")
    policy = yaml.safe_load(next(part.payload for part in original.parts if part.kind == "policy"))
    mapping = {"kind": "inline", "entries": [
        {"original": [1], "replacement": [9007199254740993]},
        {"original": [2], "replacement": [9007199254740995]}]}
    parts = [part for part in original.parts if part.kind == "mapping" and part.name == "all.csv"]
    if kind == "csv":
        mapping = {"kind": "csv", "path": "ints.csv", "source_columns": ["old"],
                   "replacement_columns": ["new"]}
        parts.append(SnapshotPart("mapping", "ints.csv",
            b"old,new\n001,9007199254740993\n002,9007199254740995\n"))
    policy["fields"][1]["behavior"] = {"action": "substitute", "mapping": mapping}
    material = prepare_csv_review_request(yaml.safe_dump(policy).encode(), source, tuple(parts),
        max_total_bytes=8192, max_review_bytes=4096, budget=GenerationBudget(5))
    assert list(csv.reader(io.StringIO(execute(material).decode()))) == [
        ["flag", "code"], ["no", "9007199254740993"], ["yes", "9007199254740995"]]
