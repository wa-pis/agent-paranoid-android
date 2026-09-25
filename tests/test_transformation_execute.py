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


def test_decimal_declaration_is_reviewed_and_never_silently_ignored():
    material = request()
    policy = yaml.safe_load(next(part.payload for part in material.parts if part.kind == "policy"))
    policy["fields"][1]["decimal_type"] = {"precision": 20, "scale": 2}
    source = next(part for part in material.parts if part.kind == "source")
    references = tuple(part for part in material.parts if part.kind == "mapping")
    material = prepare_csv_review_request(yaml.safe_dump(policy).encode(), source, references,
        max_total_bytes=8192, max_review_bytes=4096, budget=GenerationBudget(5))
    assert b'"precision": 20' in material.review
    assert b'"scale": 2' in material.review
    module = import_module("test_data_agent.io.transformation_execute")
    with pytest.raises(module.TransformationExecutionError):
        execute(material)


@pytest.mark.parametrize("replacement,expected", [("2.345", b"2.35,2.345\n"),
    ("-2.345", b"-2.35,-2.345\n"), ("2.3456", None), ("NaN", None)])
def test_exact_decimal_csv_formula(replacement, expected):
    source = SnapshotPart("source", "items", b"total,amount\n1.00,1.000\n")
    profile = csv_profile_to_dataset_profile(profile_csv_bytes(source.payload, "items", budget=GenerationBudget()))
    policy = {"schema_version": "0.1", "seed": 7,
        "schema_fingerprint": transformation_schema_fingerprint(profile), "fields": [
            {"entity": "items", "field": "total", "sensitivity": "non_sensitive",
             "decimal_type": {"precision": 20, "scale": 2},
             "behavior": {"action": "derive", "expression": "amount + 0", "dependencies": ["amount"]}},
            {"entity": "items", "field": "amount", "sensitivity": "non_sensitive",
             "decimal_type": {"precision": 20, "scale": 3},
             "behavior": {"action": "replace_text", "mapping": {"kind": "csv", "path": "m.csv",
                 "source_columns": ["old"], "replacement_columns": ["new"]}}}]}
    material = prepare_csv_review_request(yaml.safe_dump(policy).encode(), source,
        (SnapshotPart("mapping", "m.csv", f"old,new\n1.000,{replacement}\n".encode()),),
        max_total_bytes=8192, max_review_bytes=4096, budget=GenerationBudget(5))
    if expected is None:
        module = import_module("test_data_agent.io.transformation_execute")
        with pytest.raises(module.TransformationExecutionError):
            execute(material)
    else:
        assert execute(material) == b"total,amount\n" + expected


@pytest.mark.parametrize("formula", ["amount * 2", "amount / 0", "amount * 1e309", "amount + True",
    "amount + 'fictional' * 999999999999999999999999999999"])
@pytest.mark.parametrize("integer", [False, True])
def test_derive_uses_transformed_dependencies_in_topological_order(formula, integer):
    source = SnapshotPart("source", "items", b"grand,total,amount\n9,4,2\n" if integer else
                          b"grand,total,amount\n9.5,4.5,1.5\n")
    profile = csv_profile_to_dataset_profile(profile_csv_bytes(source.payload, "items", budget=GenerationBudget()))
    policy = {"schema_version": "0.1", "seed": 7,
        "schema_fingerprint": transformation_schema_fingerprint(profile), "fields": [
            {"entity": "items", "field": "grand", "sensitivity": "non_sensitive",
             "behavior": {"action": "derive", "expression": "total + amount", "dependencies": ["total", "amount"]}},
            {"entity": "items", "field": "total", "sensitivity": "non_sensitive",
             "behavior": {"action": "derive", "expression": formula, "dependencies": ["amount"]}},
            {"entity": "items", "field": "amount", "sensitivity": "non_sensitive",
             "behavior": {"action": "substitute", "mapping": {"kind": "inline", "entries": [
                 {"original": [2 if integer else 1.5], "replacement": [3 if integer else 3.5]}]}}},
        ]}
    material = prepare_csv_review_request(yaml.safe_dump(policy).encode(), source, (),
        max_total_bytes=8192, max_review_bytes=4096, budget=GenerationBudget(5))
    if formula == "amount * 2":
        assert execute(material) == (b"grand,total,amount\n9,6,3\n" if integer else
                                     b"grand,total,amount\n10.5,7.0,3.5\n")
    else:
        module = import_module("test_data_agent.io.transformation_execute")
        with pytest.raises(module.TransformationExecutionError) as caught:
            execute(material)
        assert caught.value.__context__ is None


@pytest.mark.parametrize("case", ["valid", "final_schema", "negative_mode", "null", "numeric_identity"])
@pytest.mark.parametrize("action_kind", ["synthesize", "replace_text", "substitute"])
def test_closed_synthesis_uses_bound_spec_seed_and_source_row_count(case, action_kind):
    original = request(source_bytes=(b"flag,code\ntrue,1.00\nfalse,2.00\n"
                       if case == "numeric_identity" else b"flag,code\ntrue,alpha\nfalse,beta\n"))
    source = next(part for part in original.parts if part.kind == "source")
    policy = yaml.safe_load(next(part.payload for part in original.parts if part.kind == "policy"))
    policy["fields"][1]["behavior"] = {"action": "synthesize", "generation_policy_ref": "gen.yaml"}
    if action_kind != "synthesize":
        fallback = policy["fields"][1]["behavior"]
        policy["fields"][1]["behavior"] = {"action": action_kind, "unmatched": fallback}
        if action_kind == "substitute":
            policy["fields"][1]["behavior"]["mapping"] = {"kind": "inline", "entries": [
                {"original": [3.0], "replacement": [4.0]} if case == "numeric_identity" else
                {"original": ["alpha"], "replacement": ["manual"]}]}
    spec = {"schema_version": "1.1", "entities": [{"name": "items", "row_count": 999,
        "fields": [{"name": "code", "data_type": "string"}]}],
        "generation_settings": {"seed": 999}}
    if case == "final_schema":
        spec["entities"][0]["fields"].append({"name": "flag", "data_type": "string",
            "distribution": {"kind": "string_pattern", "min_length": 8, "max_length": 8}})
        spec["validation_settings"] = {"validate_schema": False, "validate_privacy": False,
                                       "validate_relationships": False, "validate_constraints": False}
    elif case == "negative_mode":
        spec["generation_settings"]["mode"] = "negative"
    elif case == "null":
        spec["entities"][0]["fields"][0].update(nullable=True, null_ratio=1.0)
    elif case == "numeric_identity":
        spec["entities"][0]["fields"][0].update(data_type="float",
            distribution={"kind": "numeric", "min_value": 1.0, "max_value": 1.0})
    parts = tuple(part for part in original.parts if part.kind == "mapping" and part.name == "all.csv")
    if action_kind == "replace_text":
        parts = (replace(parts[0], payload=parts[0].payload + b"alpha,manual\n"),)
    parts += (SnapshotPart("generation_policy", "gen.yaml", yaml.safe_dump(spec).encode()),)
    material = prepare_csv_review_request(yaml.safe_dump(policy).encode(), source, parts,
        max_total_bytes=8192, max_review_bytes=4096, budget=GenerationBudget(5))
    if case != "valid":
        module = import_module("test_data_agent.io.transformation_execute")
        with pytest.raises(module.TransformationExecutionError) as caught:
            execute(material)
        assert caught.value.__context__ is None
        return
    first = execute(material)
    assert execute(material) == first
    rows = list(csv.DictReader(io.StringIO(first.decode())))
    assert len(rows) == 2
    assert [row["flag"] for row in rows] == ["no", "yes"]
    assert all(row["code"] not in {"alpha", "beta"} for row in rows)
    if action_kind != "synthesize":
        assert rows[0]["code"] == "manual"


def test_closed_csv_trace_reports_unmatched_without_values():
    module = import_module("test_data_agent.io.transformation_execute")
    result = module.trace_csv_replacements(request(complete=False), max_total_bytes=8192,
        max_review_bytes=4096, max_events=2, max_cells=4, max_rule_counts=4,
        budget=GenerationBudget(5))
    assert result.matched_cells == 3
    assert result.unmatched_cells == 1
    assert result.truncated and len(result.events) == 2
    assert result.rule_counts == ((1, "file", 1, 1), (2, "column", 1, 1), (2, "file", 2, 1))
    assert all(value not in repr(result) for value in ("001", "002", "second", "cascade"))


@pytest.mark.parametrize("case", ["events", "cells", "rules", "tampered"])
def test_closed_csv_trace_rejects_limits_and_tampering(case):
    module = import_module("test_data_agent.io.transformation_execute")
    material = request()
    if case == "tampered":
        material = replace(material, parts=tuple(
            replace(part, payload=part.payload + b"true,003\n") if part.kind == "source" else part
            for part in material.parts))
    with pytest.raises(module.TransformationExecutionError) as caught:
        module.trace_csv_replacements(material, max_total_bytes=8192, max_review_bytes=4096,
            max_events=0 if case == "events" else 4, max_cells=3 if case == "cells" else 4,
            max_rule_counts=1 if case == "rules" else 4, budget=GenerationBudget(5))
    assert str(caught.value) == "invalid CSV replacement trace"
    assert caught.value.__context__ is None


def test_closed_csv_trace_keeps_source_column_ordinals_after_drop():
    module = import_module("test_data_agent.io.transformation_execute")
    result = module.trace_csv_replacements(request(behavior={"action": "drop"}),
        max_total_bytes=8192, max_review_bytes=4096, max_events=4, max_cells=4,
        max_rule_counts=4, budget=GenerationBudget(5))
    assert [(event.row_ordinal, event.column_ordinal, event.scope) for event in result.events] == [
        (1, 2, "file"), (2, 2, "column")]


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
@pytest.mark.parametrize("scalar", ["string", "integer", "float", "date"])
def test_composite_domain_matches_whole_original_tuple(missing, kind, scalar):
    before, after = {
        "string": (("north", "south"), ("west", "east")),
        "integer": ((1, 2), (11, 22)),
        "float": ((1.25, 2.75), (3.125, 4.5)),
        "date": (("2025-01-01", "2025-01-02"), ("2026-01-01", "2026-01-02")),
    }[scalar]
    source = SnapshotPart("source", "items",
                          f"region,code\n{before[0]},A001\n{before[1]},A001\n".encode())
    profile = csv_profile_to_dataset_profile(profile_csv_bytes(
        source.payload, source.name, budget=GenerationBudget(5)))
    entries = [{"original": [before[0], "A001"], "replacement": [after[0], "first"]}]
    if not missing:
        entries.append({"original": [before[1], "A001"], "replacement": [after[1], "second"]})
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
            ["region", "code"], [str(after[0]), "first"], [str(after[1]), "second"]]


@pytest.mark.parametrize("kind", ["inline", "csv"])
@pytest.mark.parametrize("floating", [False, True])
def test_numeric_substitute_preserves_declared_numeric_contract(kind, floating):
    before = (1.25, 2.75) if floating else (1, 2)
    after = (2.5, 3.125) if floating else (9007199254740993, 9007199254740995)
    original = request(source_bytes=f"flag,code\ntrue,{before[0]}\nfalse,{before[1]}\n".encode())
    source = next(part for part in original.parts if part.kind == "source")
    policy = yaml.safe_load(next(part.payload for part in original.parts if part.kind == "policy"))
    mapping = {"kind": "inline", "entries": [
        {"original": [old], "replacement": [new]} for old, new in zip(before, after)]}
    parts = [part for part in original.parts if part.kind == "mapping" and part.name == "all.csv"]
    if kind == "csv":
        mapping = {"kind": "csv", "path": "ints.csv", "source_columns": ["old"],
                   "replacement_columns": ["new"]}
        text = (f"old,new\n1.25e0,{after[0]}\n2.75,{after[1]}\n" if floating else
                f"old,new\n001,{after[0]}\n002,{after[1]}\n")
        parts.append(SnapshotPart("mapping", "ints.csv", text.encode()))
    policy["fields"][1]["behavior"] = {"action": "substitute", "mapping": mapping}
    material = prepare_csv_review_request(yaml.safe_dump(policy).encode(), source, tuple(parts),
        max_total_bytes=8192, max_review_bytes=4096, budget=GenerationBudget(5))
    assert list(csv.reader(io.StringIO(execute(material).decode()))) == [
        ["flag", "code"], ["no", str(after[0])], ["yes", str(after[1])]]


@pytest.mark.parametrize("kind", ["inline", "csv"])
def test_date_substitute_keeps_canonical_iso_text(kind):
    before = ["2025-01-02", "2025-01-03"]
    after = ["2026-02-04", "2026-02-05"]
    original = request(source_bytes=f"flag,code\ntrue,{before[0]}\nfalse,{before[1]}\n".encode())
    source = next(part for part in original.parts if part.kind == "source")
    policy = yaml.safe_load(next(part.payload for part in original.parts if part.kind == "policy"))
    mapping = {"kind": "inline", "entries": [
        {"original": [old], "replacement": [new]} for old, new in zip(before, after)]}
    parts = [part for part in original.parts if part.kind == "mapping" and part.name == "all.csv"]
    if kind == "csv":
        mapping = {"kind": "csv", "path": "dates.csv", "source_columns": ["old"],
                   "replacement_columns": ["new"]}
        parts.append(SnapshotPart("mapping", "dates.csv",
            ("old,new\n" + "".join(f"{old},{new}\n" for old, new in zip(before, after))).encode()))
    policy["fields"][1]["behavior"] = {"action": "substitute", "mapping": mapping}
    material = prepare_csv_review_request(yaml.safe_dump(policy).encode(), source, tuple(parts),
        max_total_bytes=8192, max_review_bytes=4096, budget=GenerationBudget(5))
    assert list(csv.reader(io.StringIO(execute(material).decode()))) == [
        ["flag", "code"], ["no", after[0]], ["yes", after[1]]]
