import json
from argparse import Namespace
from pathlib import Path

import pytest

from test_data_agent.cli import main
from test_data_agent.core.limits import InputLimitError
from test_data_agent.core.settings import OutputFormat
from test_data_agent.io.commands import (
    generate_dataset_command,
    generate_dataset_from_csv_command,
    generate_dataset_from_example_command,
    generate_dataset_from_example_artifacts,
    generate_dataset_from_profile_command,
    generate_dataset_from_spec_path,
    infer_dataset_spec_command,
    is_dataset_spec_path,
    profile_csv_command,
    profile_example_command,
    profile_example_artifacts,
    validate_dataset_artifacts,
)
from test_data_agent.io.readers import load_dataset_spec

FIXTURE = Path(__file__).resolve().parent / "fixtures" / "example_dataset"


def test_is_dataset_spec_path_accepts_yaml_and_dataset_spec_json(tmp_path) -> None:
    yaml_path = tmp_path / "dataset_spec.yaml"
    yaml_path.write_text("entities: []\n")
    json_path = tmp_path / "dataset_spec.json"
    json_path.write_text(
        json.dumps(
            {
                "entities": [
                    {
                        "name": "customers",
                        "row_count": 1,
                        "fields": [
                            {"name": "customer_id", "data_type": "integer", "is_identifier": True},
                        ],
                    }
                ]
            }
        )
    )
    profile_path = tmp_path / "profile.json"
    profile_path.write_text(
        json.dumps(
            {
                "source_type": "csv",
                "entities": [
                    {
                        "name": "customers",
                        "row_count": 1,
                        "fields": [{"name": "customer_id", "data_type": "integer"}],
                    }
                ],
            }
        )
    )

    assert is_dataset_spec_path(yaml_path) is True
    assert is_dataset_spec_path(json_path) is True
    assert is_dataset_spec_path(profile_path) is False


def test_dataset_command_helpers_generate_and_validate_dataset_artifacts(tmp_path) -> None:
    spec_path = tmp_path / "dataset_spec.yaml"
    spec_path.write_text(
        """
entities:
  - name: customers
    row_count: 2
    primary_key: customer_id
    fields:
      - name: customer_id
        data_type: integer
        is_identifier: true
      - name: status
        data_type: string
generation_settings:
  seed: 12
  output_format: json
"""
    )
    output_folder = tmp_path / "generated"

    exit_code = generate_dataset_from_spec_path(spec_path, output_folder=output_folder)
    report = validate_dataset_artifacts(spec_path, output_folder, output_path=output_folder / "report.json")

    rows = json.loads((output_folder / "customers.json").read_text())
    written_report = json.loads((output_folder / "report.json").read_text())

    assert exit_code == 0
    assert rows[0]["customer_id"] == 12000001
    assert report.valid is True
    assert written_report["valid"] is True


def test_validate_dataset_artifacts_ignores_json_metadata_files(tmp_path) -> None:
    spec_path = tmp_path / "dataset_spec.yaml"
    spec_path.write_text(
        """
entities:
  - name: customers
    row_count: 1
    fields:
      - name: customer_id
        data_type: integer
        is_identifier: true
"""
    )
    rows_dir = tmp_path / "rows"
    rows_dir.mkdir()
    (rows_dir / "customers.json").write_text(json.dumps([{"customer_id": 1}]))
    (rows_dir / "generation_manifest.json").write_text(json.dumps({"synthetic": True}))
    (rows_dir / "validation_report.json").write_text(json.dumps({"valid": True}))

    report = validate_dataset_artifacts(spec_path, rows_dir)

    assert report.valid is True


def test_validate_dataset_artifacts_rejects_unexpected_row_files(tmp_path) -> None:
    spec_path = tmp_path / "dataset_spec.yaml"
    spec_path.write_text(
        """
entities:
  - name: customers
    row_count: 1
    fields:
      - name: customer_id
        data_type: integer
        is_identifier: true
"""
    )
    rows_dir = tmp_path / "rows"
    rows_dir.mkdir()
    (rows_dir / "customers.json").write_text(json.dumps([{"customer_id": 1}]))
    (rows_dir / "extra.json").write_text(json.dumps([{"customer_id": 2}]))

    report = validate_dataset_artifacts(spec_path, rows_dir)

    assert report.valid is False
    assert "unexpected entity: extra" in report.sections[0].errors


def test_validate_dataset_artifacts_reports_non_object_json_rows(tmp_path) -> None:
    spec_path = tmp_path / "dataset_spec.yaml"
    spec_path.write_text(
        """
entities:
  - name: customers
    row_count: 1
    fields:
      - name: customer_id
        data_type: integer
        is_identifier: true
"""
    )
    rows_dir = tmp_path / "rows"
    rows_dir.mkdir()
    (rows_dir / "customers.json").write_text(json.dumps([1]))

    report = validate_dataset_artifacts(spec_path, rows_dir)

    assert report.valid is False
    assert report.sections[0].errors == ["customers[0] row must be an object"]


def test_validate_dataset_artifacts_rejects_json_above_row_limit(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    spec_path = tmp_path / "spec.yaml"
    rows_dir = tmp_path / "rows"
    rows_dir.mkdir()
    spec_path.write_text(
        "entities:\n"
        "  - name: orders\n"
        "    row_count: 2\n"
        "    fields:\n"
        "      - name: id\n"
        "        data_type: integer\n"
    )
    (rows_dir / "orders.json").write_text('[{"id": 1}, {"id": 2}]')
    monkeypatch.setenv("TEST_DATA_AGENT_MAX_INPUT_ROWS", "1")

    with pytest.raises(InputLimitError, match="<= 1 rows"):
        validate_dataset_artifacts(spec_path, rows_dir)


def test_dataset_spec_loader_rejects_excessive_yaml_aliases(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    spec_path = tmp_path / "aliases.yaml"
    spec_path.write_text("entities: &entities []\ncopy_one: *entities\ncopy_two: *entities\n")
    monkeypatch.setenv("TEST_DATA_AGENT_MAX_YAML_ALIASES", "1")

    with pytest.raises(ValueError, match="more than 1 aliases"):
        load_dataset_spec(spec_path)


def test_validate_dataset_artifacts_rejects_symlinked_row_file(tmp_path: Path) -> None:
    spec_path = tmp_path / "spec.yaml"
    rows_dir = tmp_path / "rows"
    outside = tmp_path / "outside.json"
    rows_dir.mkdir()
    spec_path.write_text("entities: []\n")
    outside.write_text("[]")
    (rows_dir / "orders.json").symlink_to(outside)

    with pytest.raises(InputLimitError, match="symbolic link inputs are not allowed"):
        validate_dataset_artifacts(spec_path, rows_dir)


def test_generate_dataset_command_uses_dataset_spec_helper(tmp_path) -> None:
    spec_path = tmp_path / "dataset_spec.yaml"
    spec_path.write_text(
        """
entities:
  - name: customers
    row_count: 2
    primary_key: customer_id
    fields:
      - name: customer_id
        data_type: integer
        is_identifier: true
generation_settings:
  seed: 9
  output_format: json
"""
    )
    output_folder = tmp_path / "generated"

    exit_code = generate_dataset_command(
        Namespace(
            spec=spec_path,
            output=output_folder,
            output_format=None,
            seed=None,
            count=None,
        )
    )

    rows = json.loads((output_folder / "customers.json").read_text())

    assert exit_code == 0
    assert rows[0]["customer_id"] == 9000001


def test_generate_dataset_from_profile_command_writes_generation_bundle(tmp_path) -> None:
    profile_path = tmp_path / "orders_profile.json"
    output_path = tmp_path / "out" / "orders.csv"
    profile_path.write_text(
        json.dumps(
            {
                "table": "orders",
                "columns": [
                    {"name": "order_id", "data_type": "bigint", "p05": 1, "p95": 100},
                    {
                        "name": "status",
                        "data_type": "varchar",
                        "top_values": [{"value": "new"}, {"value": "shipped"}],
                        "approx_distinct_count": 2,
                    },
                ],
            }
        )
    )

    exit_code = generate_dataset_from_profile_command(
        Namespace(
            spec=None,
            profile=profile_path,
            count=4,
            seed=22,
            output=output_path,
            output_format="csv",
            mode="valid",
            invalid_ratio=0.0,
        )
    )

    assert exit_code == 0
    assert output_path.exists()
    assert json.loads((output_path.parent / "generation_spec.json").read_text())["generation_settings"]["seed"] == 22


def test_profile_example_artifacts_writes_dataset_profile_json(tmp_path) -> None:
    output_path = tmp_path / "profile.json"

    profile = profile_example_artifacts(
        FIXTURE,
        output_path=output_path,
        cache_dir=tmp_path / "cache",
    )

    payload = json.loads(output_path.read_text())

    assert profile.source_type == "csv_folder"
    assert payload["source_type"] == "csv_folder"
    assert {entity["name"] for entity in payload["entities"]} == {"customers", "orders"}


def test_generate_from_example_rejects_non_empty_output_folder(tmp_path) -> None:
    output = tmp_path / "generated"
    output.mkdir()
    (output / "stale.txt").write_text("old")

    with pytest.raises(ValueError, match="empty"):
        generate_dataset_from_example_artifacts(
            FIXTURE,
            output_folder=output,
            seed=1,
            count=2,
            output_format=OutputFormat.JSON,
            cache_dir=tmp_path / "cache",
        )


def test_generate_dataset_spec_applies_business_rules(tmp_path) -> None:
    spec_path = tmp_path / "dataset_spec.yaml"
    rules_path = tmp_path / "rules.yaml"
    output = tmp_path / "generated"
    spec_path.write_text(
        """
entities:
  - name: orders
    row_count: 1
    fields:
      - name: status
        data_type: string
"""
    )
    rules_path.write_text(
        """
field_rules:
  - table: orders
    field: status
    allowed_values: [paid]
"""
    )

    assert main(
        [
            "generate",
            str(spec_path),
            "--business-rules",
            str(rules_path),
            "--output",
            str(output),
        ]
    ) == 0

    rows = json.loads((output / "orders.json").read_text())
    assert rows[0]["status"] == "paid"
    assert (output / "business_validation_report.json").exists()


def test_profile_generation_without_output_keeps_stdout_mode(tmp_path, capsys, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    profile_path = tmp_path / "profile.json"
    profile_path.write_text(
        json.dumps(
            {
                "table": "orders",
                "columns": [{"name": "order_id", "data_type": "bigint", "p05": 1, "p95": 2}],
            }
        )
    )

    assert main(
        [
            "generate",
            "--profile",
            str(profile_path),
            "--count",
            "1",
            "--seed",
            "1",
            "--format",
            "json",
        ]
    ) == 0
    assert json.loads(capsys.readouterr().out)[0]["order_id"]


def test_profile_example_command_routes_args_to_artifact_helper(tmp_path) -> None:
    output_path = tmp_path / "profile.json"

    exit_code = profile_example_command(
        Namespace(
            input_folder=FIXTURE,
            output=output_path,
            cache_dir=tmp_path / "cache",
            no_cache=False,
            rule_sample_rows=50_000,
        )
    )

    payload = json.loads(output_path.read_text())

    assert exit_code == 0
    assert payload["source_type"] == "csv_folder"


def test_infer_dataset_spec_command_writes_dataset_spec_yaml(tmp_path) -> None:
    profile_path = tmp_path / "orders_profile.json"
    output_path = tmp_path / "dataset_spec.yaml"
    profile_path.write_text(
        json.dumps(
            {
                "table": "orders",
                "columns": [
                    {"name": "order_id", "data_type": "bigint", "p05": 1, "p95": 100},
                    {
                        "name": "status",
                        "data_type": "varchar",
                        "top_values": [{"value": "new"}, {"value": "shipped"}],
                        "approx_distinct_count": 2,
                    },
                ],
            }
        )
    )

    exit_code = infer_dataset_spec_command(
        Namespace(
            profile=profile_path,
            output=output_path,
            count=5,
        )
    )

    spec_yaml = output_path.read_text()

    assert exit_code == 0
    assert "entities:" in spec_yaml
    assert "name: orders" in spec_yaml
    assert "row_count: 5" in spec_yaml


def test_profile_csv_command_writes_dataset_profile_json(tmp_path) -> None:
    output_path = tmp_path / "profile.json"

    exit_code = profile_csv_command(
        Namespace(
            input=Path("tests/fixtures/customers.csv"),
            table="customers_alias",
            output=output_path,
        )
    )

    payload = json.loads(output_path.read_text())

    assert exit_code == 0
    assert payload["source_type"] == "csv"
    assert payload["entities"][0]["name"] == "customers_alias"


def test_generate_dataset_from_csv_command_writes_generation_bundle(tmp_path) -> None:
    output_path = tmp_path / "out" / "customers.json"

    exit_code = generate_dataset_from_csv_command(
        Namespace(
            input=Path("tests/fixtures/customers.csv"),
            count=4,
            seed=13,
            output=output_path,
            output_format="json",
            table="customers_cli",
            mode="valid",
            invalid_ratio=0.0,
        )
    )

    rows = json.loads(output_path.read_text())
    profile = json.loads((output_path.parent / "csv_profile.json").read_text())
    spec = json.loads((output_path.parent / "generation_spec.json").read_text())
    report = json.loads((output_path.parent / "validation_report.json").read_text())

    assert exit_code == 0
    assert len(rows) == 4
    assert profile["entities"][0]["name"] == "customers_cli"
    assert spec["generation_settings"]["seed"] == 13
    assert report["valid"] is True


def test_generate_dataset_from_example_artifacts_writes_review_bundle(tmp_path) -> None:
    output_folder = tmp_path / "generated"

    exit_code = generate_dataset_from_example_artifacts(
        FIXTURE,
        output_folder=output_folder,
        seed=101,
        count=4,
        output_format=OutputFormat.JSON,
        cache_dir=tmp_path / "cache",
    )

    profile = json.loads((output_folder / "profile.json").read_text())
    spec_yaml = (output_folder / "dataset_spec.yaml").read_text()
    report = json.loads((output_folder / "validation_report.json").read_text())

    assert exit_code == 0
    assert profile["source_type"] == "csv_folder"
    assert "entities:" in spec_yaml
    assert "customers" in spec_yaml
    assert report["valid"] is True


def test_generate_dataset_from_example_command_routes_args_to_artifact_helper(tmp_path) -> None:
    output_folder = tmp_path / "generated"

    exit_code = generate_dataset_from_example_command(
        Namespace(
            input_folder=FIXTURE,
            output=output_folder,
            seed=101,
            count=4,
            output_format="json",
            cache_dir=tmp_path / "cache",
            no_cache=False,
            rule_sample_rows=50_000,
        )
    )

    report = json.loads((output_folder / "validation_report.json").read_text())

    assert exit_code == 0
    assert report["valid"] is True
