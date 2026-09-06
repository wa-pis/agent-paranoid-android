"""Regression checks for reviewed generation contracts; artificial data only."""

from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

from test_data_agent.cli import main
from test_data_agent.core.constraint import Constraint
from test_data_agent.core.dataset import DatasetProfile, DatasetSpec
from test_data_agent.core.entity import EntitySpec
from test_data_agent.core.field import FieldSpec
from test_data_agent.core.relationship import Relationship
from test_data_agent.core.settings import (
    GenerationMode,
    OutputFormat,
    ValidationSettings,
)
from test_data_agent.generation.entity_generator import generate_dataset
from test_data_agent.io.workflows import (
    generate_dataset_bundle,
    generate_single_entity_profile_artifacts,
)
from test_data_agent.validation import validate_dataset


def formula_spec() -> DatasetSpec:
    return DatasetSpec(
        entities=[
            EntitySpec(
                name="items",
                row_count=3,
                fields=[
                    FieldSpec(name=name, data_type="integer")
                    for name in ("a", "b", "c")
                ],
            )
        ],
        constraints=[
            Constraint(
                type="formula",
                entity="items",
                fields=[target],
                expression=expression,
                confidence=1,
                status="confirmed",
            )
            for target, expression in (("c", "b * 2"), ("b", "a * 2"))
        ],
    )


def test_formula_dependencies_are_ordered_and_reproducible() -> None:
    spec = formula_spec()
    rows = generate_dataset(spec, seed=1)
    assert all(row["c"] == row["b"] * 2 == row["a"] * 4 for row in rows["items"])
    assert rows == generate_dataset(spec, seed=1)
    assert validate_dataset(rows, spec).valid


@pytest.mark.parametrize("cycle", [False, True])
def test_formula_conflicts_fail_before_publication(tmp_path: Path, cycle: bool) -> None:
    spec = formula_spec()
    if cycle:
        spec.constraints[1].expression = "c * 2"
    else:
        spec.constraints.append(spec.constraints[0].model_copy(deep=True))
    with pytest.raises(ValueError, match="cyclic formula|duplicate formula"):
        generate_dataset_bundle(spec, output_folder=tmp_path / "output", seed=1)
    assert not (tmp_path / "output").exists()


def test_rejected_formula_is_neither_applied_nor_validated() -> None:
    spec = formula_spec()
    spec.constraints[0].status = "rejected"
    spec.constraints[0].expression = "b / 0"
    rows = generate_dataset(spec, seed=1)
    assert validate_dataset(rows, spec).valid


def relationship_spec(*, identifier: bool = False) -> DatasetSpec:
    return DatasetSpec(
        entities=[
            EntitySpec(
                name="parents",
                row_count=2,
                primary_key="id",
                fields=[FieldSpec(name="id", data_type="integer", is_identifier=True)],
            ),
            EntitySpec(
                name="children",
                row_count=8,
                fields=[
                    FieldSpec(
                        name="parent_id",
                        data_type="integer",
                        nullable=True,
                        null_ratio=0.5,
                        is_identifier=identifier,
                    )
                ],
            ),
        ],
        relationships=[
            Relationship(
                parent_entity="parents",
                parent_field="id",
                child_entity="children",
                child_field="parent_id",
                confidence=1,
            )
        ],
    )


@pytest.mark.parametrize("identifier", [False, True])
@pytest.mark.parametrize("ratio", [0, 0.5, 1])
def test_nullable_relationships_preserve_nulls(identifier: bool, ratio: float) -> None:
    spec = relationship_spec(identifier=identifier)
    spec.entities[1].fields[0].null_ratio = ratio
    unlinked = spec.model_copy(deep=True)
    unlinked.relationships = []
    before = generate_dataset(unlinked, seed=1)["children"]
    rows = generate_dataset(spec, seed=1)
    assert [row["parent_id"] is None for row in rows["children"]] == [
        row["parent_id"] is None for row in before
    ]
    assert validate_dataset(rows, spec).valid


def test_nullable_one_to_one_counts_only_present_children() -> None:
    spec = relationship_spec()
    spec.relationships[0].relationship_type = "one_to_one"
    spec.entities[1].fields[0].null_ratio = 1
    rows = generate_dataset(spec, seed=1)
    assert validate_dataset(rows, spec).valid


def test_rejected_relationship_does_not_wire_or_validate() -> None:
    spec = relationship_spec()
    spec.relationships[0].status = "rejected"
    rows = generate_dataset(spec, seed=1)
    unlinked = spec.model_copy(deep=True)
    unlinked.relationships = []
    assert rows == generate_dataset(unlinked, seed=1)
    assert validate_dataset(rows, spec).valid


def test_required_identifier_rejects_null_even_without_primary_key() -> None:
    spec = DatasetSpec(
        entities=[
            EntitySpec(
                name="items",
                row_count=1,
                fields=[
                    FieldSpec(name="ref_id", data_type="integer", is_identifier=True)
                ],
            )
        ]
    )
    assert not validate_dataset({"items": [{"ref_id": None}]}, spec).valid


@pytest.mark.parametrize("length", [1, 3, 4, 5, 12])
def test_string_pattern_counts_complete_output(length: int) -> None:
    spec = DatasetSpec(
        entities=[
            EntitySpec(
                name="items",
                row_count=5,
                fields=[
                    FieldSpec(
                        name="label",
                        data_type="string",
                        distribution={
                            "kind": "string_pattern",
                            "min_length": length,
                            "max_length": length,
                        },
                    )
                ],
            )
        ]
    )
    rows = generate_dataset(spec, seed=1)
    assert all(len(row["label"]) == length for row in rows["items"])
    rows["items"][0]["label"] += "x"
    assert not validate_dataset(rows, spec).valid


def test_privacy_revalidation_inspects_rows_without_echoing_values() -> None:
    spec = DatasetSpec(
        entities=[
            EntitySpec(
                name="items",
                row_count=1,
                fields=[
                    FieldSpec(
                        name="email",
                        data_type="string",
                        sensitive=True,
                        semantic_type="email",
                    )
                ],
            )
        ]
    )
    value = "fictional-person@example.invalid"
    report = validate_dataset({"items": [{"email": value}]}, spec)
    assert not report.valid
    assert next(
        section for section in report.sections if section.name == "privacy"
    ).failed
    assert value not in report.model_dump_json()
    assert validate_dataset(generate_dataset(spec, seed=1), spec).valid


@pytest.mark.parametrize("mode", list(GenerationMode))
def test_privacy_checked_after_business_mutation_in_every_mode(
    tmp_path: Path, mode: GenerationMode
) -> None:
    spec = DatasetSpec(
        entities=[
            EntitySpec(
                name="items",
                row_count=1,
                fields=[FieldSpec(name="label", data_type="string")],
            )
        ]
    )
    spec.generation_settings.mode = mode
    spec.validation_settings = ValidationSettings(validate_privacy=False)

    def mutate(rows: dict[str, list[dict[str, Any]]], seed: int) -> None:
        rows["items"][0]["label"] = "fictional-person@example.invalid"

    with pytest.raises(ValueError, match="privacy validation"):
        generate_dataset_bundle(
            spec, output_folder=tmp_path / "output", business_rules_applier=mutate
        )
    assert not (tmp_path / "output").exists()


def test_post_business_constraint_failure_cannot_publish_with_disabled_report(
    tmp_path: Path,
) -> None:
    spec = formula_spec()
    spec.validation_settings = ValidationSettings(validate_constraints=False)

    def mutate(rows: dict[str, list[dict[str, Any]]], seed: int) -> None:
        rows["items"][0]["c"] = -1

    with pytest.raises(ValueError, match="constraint validation"):
        generate_dataset_bundle(
            spec, output_folder=tmp_path / "output", business_rules_applier=mutate
        )
    assert not (tmp_path / "output").exists()


def test_business_report_failure_blocks_valid_bundle(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="business validation"):
        generate_dataset_bundle(
            formula_spec(),
            output_folder=tmp_path / "output",
            business_rules_applier=lambda rows, seed: SimpleNamespace(valid=False),
        )
    assert not (tmp_path / "output").exists()


def test_single_file_rejection_preserves_existing_output(tmp_path: Path) -> None:
    spec = formula_spec()
    spec.generation_settings.output_format = OutputFormat.JSON
    output = tmp_path / "items.json"
    output.write_text("[]")
    rows = generate_dataset(spec, seed=1)
    rows["items"][0]["c"] = -1
    with pytest.raises(ValueError, match="constraint validation"):
        generate_single_entity_profile_artifacts(
            DatasetProfile(),
            spec,
            output_path=output,
            rows_by_entity=rows,
            overwrite=True,
        )
    assert output.read_text() == "[]"


def test_cli_and_mcp_reject_cycle_before_publishing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from test_data_agent.mcp_generator_server import generate_dataset as mcp_generate

    spec = formula_spec()
    spec.constraints[1].expression = "c * 2"
    source = tmp_path / "spec.json"
    source.write_text(spec.model_dump_json())
    assert main(["generate", str(source), "--output", str(tmp_path / "cli")]) != 0
    monkeypatch.setenv("TEST_DATA_AGENT_WORKSPACE_ROOT", str(tmp_path))
    with pytest.raises(ValueError, match="cyclic formula"):
        mcp_generate(spec_path="spec.json", output_folder="mcp")
    assert not (tmp_path / "cli").exists()
    assert not (tmp_path / "mcp").exists()
