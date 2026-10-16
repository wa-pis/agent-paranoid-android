"""Boundary regressions for portable scalar values, rules and bounded decoding."""

from decimal import Decimal
import json

import pytest

from test_data_agent.core.dataset import DatasetProfile, DatasetSpec
from test_data_agent.core.entity import EntityProfile
from test_data_agent.core.field import FieldProfile
from test_data_agent.core.limits import InputLimitError
from test_data_agent.core.settings import OutputFormat
from test_data_agent.io.artifacts import write_generation_manifest
from test_data_agent.io.readers import load_dataset_rows, load_dataset_spec
from test_data_agent.io.sql_rows import read_insert_rows
from test_data_agent.io.workflows import (
    generate_dataset_from_profile_artifacts,
    generate_dataset_bundle,
)
from test_data_agent.io.writers import write_dataset_rows, rows_to_sql
from test_data_agent.profiling.budget import LocalProfileBudget
from test_data_agent.validation import validate_dataset


@pytest.mark.parametrize("output", list(OutputFormat))
def test_null_empty_text_and_typed_conditions_roundtrip_without_mutation(
    tmp_path, output
):
    spec = DatasetSpec.model_validate(
        {
            "entities": [
                {
                    "name": "records",
                    "row_count": 1,
                    "fields": [
                        {"name": "active", "data_type": "boolean"},
                        {"name": "day", "data_type": "date"},
                        {"name": "at", "data_type": "datetime"},
                        {"name": "label", "data_type": "string", "nullable": True},
                        {"name": "optional", "data_type": "string", "nullable": True},
                        {"name": "required", "data_type": "string"},
                    ],
                }
            ],
            "constraints": [
                {
                    "type": "conditional_required",
                    "entity": "records",
                    "fields": ["required"],
                    "condition": {"field": "active", "equals": True},
                    "confidence": 1,
                }
            ],
            "business_rules": {
                "row_rules": [
                    {
                        "type": "conditional_allowed_values",
                        "table": "records",
                        "field": "label",
                        "when": {"field": "optional", "equals": None},
                        "allowed_values": [""],
                    },
                    {
                        "type": "conditional_required",
                        "table": "records",
                        "when": {"field": "active", "equals": True},
                        "required_fields": ["required"],
                    },
                    {
                        "type": "conditional_required",
                        "table": "records",
                        "when": {"field": "day", "equals": "2024-01-01"},
                        "required_fields": ["required"],
                    },
                    {
                        "type": "conditional_required",
                        "table": "records",
                        "when": {"field": "at", "equals": "2024-01-01T01:02:03"},
                        "required_fields": ["required"],
                    },
                ]
            },
        }
    )
    rows = {
        "records": [
            dict(
                active=True,
                day="2024-01-01",
                at="2024-01-01T01:02:03",
                label="",
                optional=None,
                required="ready",
            )
        ]
    }
    write_dataset_rows(rows, output, tmp_path, spec=spec)
    write_generation_manifest(
        spec,
        seed=0,
        output_format=output,
        row_counts={"records": 1},
        validation_valid=True,
        output_folder=tmp_path,
    )
    reloaded = load_dataset_rows(tmp_path)
    assert reloaded["records"][0]["label"] == ""
    assert reloaded["records"][0]["optional"] is None
    assert validate_dataset(reloaded, spec).valid
    reloaded["records"][0]["required"] = None
    before = dict(reloaded["records"][0])
    report = validate_dataset(reloaded, spec)
    assert not report.valid
    assert (
        next(
            section for section in report.sections if section.name == "constraints"
        ).failed
        == 1
    )
    assert not report.business_validation.valid
    assert [result.failed for result in report.business_validation.results] == [
        0,
        1,
        1,
        1,
    ]
    assert reloaded["records"][0] == before


def test_csv_escape_markers_headers_and_spreadsheet_formulas_are_reversible(tmp_path):
    values = [
        None,
        "",
        r"\N",
        r"\Fready",
        r"\\ready",
        "=1+2",
        "\tfictional",
        "-7",
        "'ready",
    ]
    spec = DatasetSpec.model_validate(
        {
            "entities": [
                {
                    "name": "records",
                    "row_count": len(values),
                    "fields": [
                        {"name": "=label", "data_type": "string", "nullable": True}
                    ],
                }
            ]
        }
    )
    rows = {"records": [{"=label": value} for value in values]}
    write_dataset_rows(rows, OutputFormat.CSV, tmp_path, spec=spec)
    write_generation_manifest(
        spec,
        seed=0,
        output_format=OutputFormat.CSV,
        row_counts={"records": len(values)},
        validation_valid=True,
        output_folder=tmp_path,
    )
    assert load_dataset_rows(tmp_path) == rows
    assert (tmp_path / "records.csv").read_text().startswith(r"\F=label")
    (tmp_path / "generation_manifest.json").unlink()
    assert load_dataset_rows(tmp_path)["records"][0] == {r"\F=label": r"\N"}


@pytest.mark.parametrize("output", list(OutputFormat))
def test_single_profile_custom_filename_preserves_entity_mapping(tmp_path, output):
    profile = DatasetProfile(
        entities=[
            EntityProfile(
                name="records",
                row_count=2,
                fields=[FieldProfile(name="amount", data_type="integer")],
            )
        ]
    )
    target = tmp_path / f"custom.{output.value}"
    report, _ = generate_dataset_from_profile_artifacts(
        profile, count=3, seed=17, output_path=target, output_format=output
    )
    assert report.valid
    rows = load_dataset_rows(tmp_path)
    assert set(rows) == {"records"}
    assert validate_dataset(
        rows, load_dataset_spec(tmp_path / "dataset_spec.json")
    ).valid


def test_sql_data_reader_preserves_quotes_newlines_literals_and_precision():
    row = {
        "label": "fictional 'quote';\nSELECT 1",
        'quoted"field': None,
        "flag": True,
        "amount": Decimal("9007199254740993.1250"),
        "integer": 7,
    }
    rows = read_insert_rows(
        rows_to_sql("records", [row]), "records", budget=LocalProfileBudget()
    )
    assert rows == [{**row, "amount": "9007199254740993.1250", "integer": "7"}]


@pytest.mark.parametrize(
    "sql",
    [
        "SELECT 1;",
        "DROP TABLE records;",
        "INSERT INTO records (x) VALUES (1);",
        'INSERT INTO "other" ("x") VALUES (1);',
        'INSERT INTO "records" ("x", "x") VALUES (1, 2);',
        'INSERT INTO "records" ("x") VALUES (1); SELECT 1;',
        'INSERT INTO "records" ("x") VALUES (secret_marker);',
    ],
)
def test_sql_data_reader_rejects_other_grammar_without_echoing_values(sql):
    with pytest.raises(
        ValueError, match="^SQL dataset input accepts only generated INSERT statements$"
    ):
        read_insert_rows(sql, "records", budget=LocalProfileBudget())


def test_sql_rows_share_dataset_limits_and_deadlines(tmp_path, monkeypatch):
    monkeypatch.setenv("TEST_DATA_AGENT_MAX_INPUT_ROWS", "1")
    for name in ("first", "second"):
        (tmp_path / f"{name}.sql").write_text(rows_to_sql(name, [{"x": "fictional"}]))
    with pytest.raises(InputLimitError):
        load_dataset_rows(tmp_path)
    budget = LocalProfileBudget()
    monkeypatch.setattr(
        LocalProfileBudget,
        "check_deadline",
        lambda *args: (_ for _ in ()).throw(TimeoutError("deadline")),
    )
    with pytest.raises(TimeoutError):
        read_insert_rows(
            rows_to_sql("records", [{"x": "fictional"}]), "records", budget=budget
        )


@pytest.mark.parametrize("output", list(OutputFormat))
def test_maximum_seed_integer_identifiers_roundtrip_every_output(tmp_path, output):
    spec = DatasetSpec.model_validate(
        {
            "entities": [
                {
                    "name": "records",
                    "row_count": 2,
                    "fields": [
                        {"name": "id", "data_type": "integer", "is_identifier": True}
                    ],
                }
            ],
            "generation_settings": {"seed": 2**63 - 1, "output_format": output},
        }
    )
    assert generate_dataset_bundle(
        spec, output_folder=tmp_path / "bundle"
    ).validation.valid
    assert validate_dataset(load_dataset_rows(tmp_path / "bundle"), spec).valid


@pytest.mark.parametrize("encoding", ["invalid", {"nested": True}])
def test_unknown_csv_encoding_rejected(tmp_path, encoding):
    (tmp_path / "generation_manifest.json").write_text(
        json.dumps({"csv_encoding": encoding})
    )
    with pytest.raises(ValueError, match="unsupported CSV scalar encoding"):
        load_dataset_rows(tmp_path)


@pytest.mark.parametrize(
    "encoding,value",
    [
        (b"unknown", '"fictional"'),
        (b"json-v1", '{"nested": "fictional"}'),
        (b"integer-text-v1", "fictional"),
    ],
)
def test_parquet_codec_rejects_unknown_or_non_scalar_cells(tmp_path, encoding, value):
    pa = pytest.importorskip("pyarrow")
    pq = pytest.importorskip("pyarrow.parquet")
    schema = pa.schema(
        [pa.field("value", pa.string(), metadata={b"apa.scalar_encoding": encoding})]
    )
    pq.write_table(
        pa.Table.from_pylist([{"value": value}], schema=schema),
        tmp_path / "records.parquet",
    )
    with pytest.raises(ValueError, match="Parquet (scalar|integer) encoding"):
        load_dataset_rows(tmp_path)


@pytest.mark.parametrize(
    "variable", ["TEST_DATA_AGENT_MAX_INPUT_CELLS", "TEST_DATA_AGENT_MAX_INPUT_COLUMNS"]
)
def test_sql_column_and_cell_limits_are_enforced(variable, monkeypatch):
    monkeypatch.setenv(variable, "1")
    with pytest.raises(InputLimitError):
        read_insert_rows(
            rows_to_sql("records", [{"one": 1, "two": 2}]),
            "records",
            budget=LocalProfileBudget(),
        )


def test_sql_cell_size_limit_is_enforced(monkeypatch):
    monkeypatch.setenv("TEST_DATA_AGENT_MAX_INPUT_CELL_CHARS", "10")
    with pytest.raises(ValueError, match="SQL dataset cell exceeds limit"):
        read_insert_rows(
            rows_to_sql("records", [{"one": "x" * 11}]),
            "records",
            budget=LocalProfileBudget(),
        )


@pytest.mark.parametrize(
    "mapping",
    [
        {"records": "../outside.csv"},
        {"records": {"nested": True}},
        {"first": "records.csv", "second": "records.csv"},
        [],
    ],
)
def test_invalid_entity_artifact_mapping_is_rejected(tmp_path, mapping):
    (tmp_path / "generation_manifest.json").write_text(
        json.dumps({"entity_artifacts": mapping})
    )
    with pytest.raises(ValueError, match="invalid entity artifact mapping"):
        load_dataset_rows(tmp_path)


@pytest.mark.parametrize("output", list(OutputFormat))
def test_cli_multi_profile_writes_all_entities(tmp_path, output):
    from test_data_agent.cli import main

    profile = DatasetProfile(
        entities=[
            EntityProfile(
                name=name,
                row_count=2,
                fields=[FieldProfile(name="amount", data_type="integer")],
            )
            for name in ("first", "second")
        ]
    )
    path = tmp_path / "profile.json"
    path.write_text(profile.model_dump_json())
    target = tmp_path / "bundle"
    assert (
        main(
            [
                "generate",
                "--profile",
                str(path),
                "--count",
                "3",
                "--seed",
                "7",
                "--mode",
                "load_test",
                "--format",
                output.value,
                "--output",
                str(target),
            ]
        )
        == 0
    )
    assert {name: len(rows) for name, rows in load_dataset_rows(target).items()} == {
        "first": 3,
        "second": 3,
    }


def test_multi_profile_overwrite_cannot_remove_its_input(tmp_path, capsys):
    from test_data_agent.cli import main

    profile = DatasetProfile(
        entities=[
            EntityProfile(
                name=name,
                row_count=2,
                fields=[FieldProfile(name="amount", data_type="integer")],
            )
            for name in ("first", "second")
        ]
    )
    path = tmp_path / "profile.json"
    path.write_text(profile.model_dump_json())
    original = path.read_bytes()
    assert (
        main(
            [
                "generate",
                "--profile",
                str(path),
                "--count",
                "3",
                "--seed",
                "7",
                "--output",
                str(tmp_path),
                "--overwrite",
            ]
        )
        == 2
    )
    assert "must not contain the input profile" in capsys.readouterr().err
    assert path.read_bytes() == original
