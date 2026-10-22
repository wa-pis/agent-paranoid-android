"""Reviewed per-entity counts and inference-only total row ceilings."""

import pytest

from test_data_agent.cli import main
from test_data_agent.core.dataset import DatasetProfile
from test_data_agent.core.entity import EntityProfile
from test_data_agent.core.field import FieldProfile
from test_data_agent.core.relationship import Relationship
from test_data_agent.generation import generate_dataset, infer_dataset_spec
from test_data_agent.io.workflows import infer_dataset_spec_artifact
from test_data_agent.adapters.json_profile import load_json_dataset_spec
from test_data_agent.validation import validate_dataset


def relational_profile() -> DatasetProfile:
    return DatasetProfile(entities=[
        EntityProfile(name="parents", row_count=2, primary_key_candidates=["id"], fields=[
            FieldProfile(name="id", data_type="integer", is_identifier=True),
        ]),
        EntityProfile(name="children", row_count=5, fields=[
            FieldProfile(name="parent_id", data_type="integer", is_identifier=True,
                         nullable=True, null_ratio=0.2),
        ]),
    ], relationships=[Relationship(
        parent_entity="parents", parent_field="id", child_entity="children",
        child_field="parent_id", confidence=1, status="declared",
    )])


def test_entity_counts_override_global_count_without_mutating_profile():
    profile = relational_profile()
    original = profile.model_dump_json()
    spec = infer_dataset_spec(profile, count=9, entity_counts={"parents": 3}, max_total_rows=12)
    assert [entity.row_count for entity in spec.entities] == [3, 9]
    assert profile.model_dump_json() == original
    assert [entity.row_count for entity in infer_dataset_spec(profile).entities] == [2, 5]
    assert [entity.row_count for entity in infer_dataset_spec(profile, count=4).entities] == [4, 4]
    rows = generate_dataset(spec, seed=7)
    assert [len(rows[name]) for name in ("parents", "children")] == [3, 9]
    assert rows == generate_dataset(spec, seed=7)
    parent_keys = {row["id"] for row in rows["parents"]}
    assert all(row["parent_id"] is None or row["parent_id"] in parent_keys
               for row in rows["children"])
    assert validate_dataset(rows, spec).valid


@pytest.mark.parametrize("value", [True, 0, -1, 1.5, "5"])
def test_entity_counts_require_strict_positive_integers(value):
    with pytest.raises(ValueError, match="entity counts must be positive integers"):
        infer_dataset_spec(relational_profile(), entity_counts={"parents": value})


@pytest.mark.parametrize("value", [True, 0, -1, 1.5, "5"])
def test_total_row_ceiling_requires_strict_positive_integer(value):
    with pytest.raises(ValueError, match="maximum total rows must be a positive integer"):
        infer_dataset_spec(relational_profile(), max_total_rows=value)


def test_unknown_entity_rejects_without_echoing_input():
    with pytest.raises(ValueError, match="entity counts must reference existing profile entities") as error:
        infer_dataset_spec(relational_profile(), entity_counts={"private-value": 5})
    assert "private-value" not in str(error.value)


def test_total_row_ceiling_rejects_before_field_inference(monkeypatch):
    def unexpected(*args):
        pytest.fail("field inference must not start for an oversized plan")

    monkeypatch.setattr("test_data_agent.generation.planner._infer_field", unexpected)
    with pytest.raises(ValueError, match="planned total rows exceed maximum total rows"):
        infer_dataset_spec(relational_profile(), entity_counts={"children": 100}, max_total_rows=10)


def test_failed_total_row_ceiling_leaves_existing_artifact_unchanged(tmp_path):
    output = tmp_path / "spec.json"
    output.write_text("previous-artifact")
    with pytest.raises(ValueError, match="planned total rows"):
        infer_dataset_spec_artifact(relational_profile(), output_path=output, max_total_rows=6)
    assert output.read_text() == "previous-artifact"


def test_cli_per_entity_sizing_round_trips_reviewed_spec(tmp_path):
    profile_path = tmp_path / "profile.json"
    output = tmp_path / "spec.json"
    profile_path.write_text(relational_profile().model_dump_json())
    assert main(["infer-spec", str(profile_path), "--output", str(output),
                 "--count", "10", "--entity-count", "parents=3",
                 "--entity-count", "children=12", "--max-total-rows", "15"]) == 0
    spec = load_json_dataset_spec(output)
    assert [entity.row_count for entity in spec.entities] == [3, 12]
    assert "max_total_rows" not in output.read_text()
    generated = generate_dataset(spec, seed=7)
    assert validate_dataset(generated, spec).valid


@pytest.mark.parametrize("arguments", [
    ["--entity-count", "parents=3", "--entity-count", "parents=4"],
    ["--entity-count", "unknown=3"],
    ["--max-total-rows", "6"],
])
def test_cli_invalid_sizing_publishes_no_spec(tmp_path, arguments):
    profile_path = tmp_path / "profile.json"
    output = tmp_path / "spec.json"
    profile_path.write_text(relational_profile().model_dump_json())
    assert main(["infer-spec", str(profile_path), "--output", str(output), *arguments]) == 2
    assert not output.exists()


@pytest.mark.parametrize("value", ["parents=0", "parents=-1", "parents=1.5", "=3", "parents", "parents=private-value"])
def test_cli_malformed_count_is_fixed_error_and_creates_no_spec(tmp_path, capsys, value):
    output = tmp_path / "spec.json"
    with pytest.raises(SystemExit) as error:
        main(["infer-spec", str(tmp_path / "absent.json"), "--output", str(output),
              "--entity-count", value])
    assert error.value.code == 2
    assert "private-value" not in capsys.readouterr().err
    assert not output.exists()
