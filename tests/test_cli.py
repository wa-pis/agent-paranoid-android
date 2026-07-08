import csv
import json

from test_data_agent.cli import main


def test_generate_from_profile_writes_data_spec_and_report(tmp_path) -> None:
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
                    {
                        "name": "created_at",
                        "data_type": "timestamp",
                        "min_timestamp": "2024-01-01T00:00:00",
                        "max_timestamp": "2024-01-02T00:00:00",
                    },
                ],
            }
        )
    )

    exit_code = main(
        [
            "generate",
            "--profile",
            str(profile_path),
            "--count",
            "10",
            "--mode",
            "mixed",
            "--invalid-ratio",
            "0.25",
            "--seed",
            "12345",
            "--format",
            "csv",
            "--output",
            str(output_path),
        ]
    )

    assert exit_code == 0
    assert output_path.exists()

    with output_path.open() as handle:
        rows = list(csv.DictReader(handle))

    spec = json.loads((output_path.parent / "generation_spec.json").read_text())
    report = json.loads((output_path.parent / "validation_report.json").read_text())

    assert len(rows) == 10
    assert spec["seed"] == 12345
    assert spec["output_format"] == "csv"
    assert spec["table"]["row_count"] == 10
    assert all(column["invalid_ratio"] == 0.25 for column in spec["table"]["columns"])
    assert report["row_count"] == 10
    assert report["expected_row_count"] == 10
    assert report["error_count"] > 0
