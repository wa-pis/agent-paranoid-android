import csv
import json
from pathlib import Path

from test_data_agent.adapters import load_profile_or_spec
from test_data_agent.core.dataset import DatasetProfile
from test_data_agent.core.settings import OutputFormat
from test_data_agent.io import generate_dataset_bundle, infer_dataset_spec_artifact
from test_data_agent.safety import assert_profile_safe


PROJECT_ROOT = Path(__file__).parent.parent


def test_safe_trino_profile_to_synthetic_csv_e2e(tmp_path: Path) -> None:
    profile_path = PROJECT_ROOT / "examples" / "trino_safe_profile.json"
    loaded = load_profile_or_spec(profile_path)

    assert isinstance(loaded, DatasetProfile)
    assert_profile_safe(loaded)
    assert "@" not in loaded.model_dump_json()

    spec = infer_dataset_spec_artifact(
        loaded,
        output_path=tmp_path / "dataset_spec.yaml",
        count=12,
    )
    result = generate_dataset_bundle(
        spec,
        output_folder=tmp_path / "generated",
        output_format=OutputFormat.CSV,
        seed=12345,
    )

    with (tmp_path / "generated" / "orders.csv").open() as handle:
        rows = list(csv.DictReader(handle))
    validation = json.loads((tmp_path / "generated" / "validation_report.json").read_text())
    manifest = json.loads((tmp_path / "generated" / "generation_manifest.json").read_text())

    assert result.validation.valid is True
    assert len(rows) == 12
    assert rows[0]["order_id"].startswith("12345")
    assert rows[0]["customer_email"]
    assert all(row["customer_email"].endswith("@example.test") for row in rows)
    assert validation["valid"] is True
    assert manifest["source_rows_copied"] is False
    assert manifest["synthetic"] is True
    assert manifest["seed"] == 12345
