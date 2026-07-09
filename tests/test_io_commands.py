import json

from test_data_agent.io.commands import (
    generate_dataset_from_spec_path,
    is_dataset_spec_path,
    validate_dataset_artifacts,
)


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
