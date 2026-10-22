"""Synthetic relational acceptance through direct services and CLI artifacts."""
import json

import pytest

from test_data_agent.cli import main
from test_data_agent.core.dataset import DatasetSpec
from test_data_agent.generation.entity_generator import generate_dataset
from test_data_agent.validation import validate_dataset


def relational_spec(parents=2, children=7, null_ratio=0.0):
    return DatasetSpec.model_validate({
        "entities": [
            {"name": "parent", "row_count": parents, "fields": [
                {"name": "key", "data_type": "integer", "is_identifier": True}]},
            {"name": "child", "row_count": children, "fields": [
                {"name": "parent_key", "data_type": "integer", "nullable": True,
                 "null_ratio": null_ratio},
                {"name": "own_key", "data_type": "integer", "is_identifier": True}]}],
        "relationships": [{"parent_entity": "parent", "parent_field": "key",
                           "child_entity": "child", "child_field": "parent_key", "confidence": 1}],
    })


@pytest.mark.parametrize("parents,children", [(2, 7), (7, 2)])
@pytest.mark.parametrize("null_ratio", [0.0, 1.0])
def test_unequal_sizes_nullable_keys_and_replay_match_cli(tmp_path, parents, children, null_ratio):
    spec = relational_spec(parents, children, null_ratio)
    before = spec.model_dump(mode="json")
    rows = generate_dataset(spec, seed=27)
    assert rows == generate_dataset(spec, seed=27)
    assert spec.model_dump(mode="json") == before
    assert {name: len(items) for name, items in rows.items()} == {"parent": parents, "child": children}
    parent_keys = {row["key"] for row in rows["parent"]}
    assert parent_keys.isdisjoint(row["own_key"] for row in rows["child"])
    assert all(row["parent_key"] is None if null_ratio else row["parent_key"] in parent_keys
               for row in rows["child"])
    assert validate_dataset(rows, spec).valid
    path = tmp_path / "spec.json"
    path.write_text(spec.model_dump_json())
    for name in ("first", "second"):
        out = tmp_path / name
        assert main(["generate", str(path), "--output", str(out), "--format", "json", "--seed", "27"]) == 0
        for entity, expected in rows.items():
            assert json.loads((out / f"{entity}.json").read_text()) == expected
        report = json.loads((out / "validation_report.json").read_text())
        assert report["valid"]
    assert (tmp_path / "first/validation_report.json").read_bytes() == (tmp_path / "second/validation_report.json").read_bytes()


@pytest.mark.parametrize("parent_rows,child_rows,relationship_valid", [
    ([], [], True),
    ([], [{"parent_key": None, "own_key": 2}], True),
    ([], [{"parent_key": 1, "own_key": 2}], False),
    ([{"key": 1}], [], True),
])
def test_empty_relations_validate_consistently_in_cli(tmp_path, parent_rows, child_rows, relationship_valid):
    spec = relational_spec()
    rows = {"parent": parent_rows, "child": child_rows}
    direct = validate_dataset(rows, spec)
    assert not direct.valid  # Empty tables do not satisfy the positive declared row counts.
    relationships = next(s for s in direct.sections if s.name == "relationships")
    assert (relationships.failed == 0) is relationship_valid
    path = tmp_path / "spec.json"
    path.write_text(spec.model_dump_json())
    folder = tmp_path / "rows"
    folder.mkdir()
    (folder / "parent.csv").write_text("key\n" + "".join(f"{r['key']}\n" for r in parent_rows))
    (folder / "child.csv").write_text("parent_key,own_key\n" + "".join(
        f"{'' if r['parent_key'] is None else r['parent_key']},{r['own_key']}\n" for r in child_rows))
    before = {p.name: p.read_bytes() for p in folder.iterdir()}
    report_path = tmp_path / "report.json"
    assert main(["validate", str(path), str(folder), "--output", str(report_path)]) == 1
    report = json.loads(report_path.read_text())
    assert not report["valid"]
    cli_relationships = next(s for s in report["sections"] if s["name"] == "relationships")
    assert (cli_relationships["failed"] == 0) is relationship_valid
    assert cli_relationships["relationship_metrics"] == [m.model_dump(mode="json") for m in relationships.relationship_metrics]
    assert {p.name: p.read_bytes() for p in folder.iterdir()} == before
