from __future__ import annotations

import json
from pathlib import Path

from test_data_agent.io import GenerationManifest, load_dataset_spec
from test_data_agent.io.artifacts import dataset_spec_fingerprint
from test_data_agent.io.workflows import generate_dataset_bundle


FIXTURE_ROOT = Path("tests/fixtures/compatibility/v0.11.0")


def test_current_package_reads_and_generates_from_v0_11_contracts(
    tmp_path: Path,
) -> None:
    spec = load_dataset_spec(FIXTURE_ROOT / "dataset-spec.json")
    previous_manifest = GenerationManifest.model_validate_json(
        (FIXTURE_ROOT / "generation-manifest.json").read_text()
    )

    assert dataset_spec_fingerprint(spec) == previous_manifest.spec_sha256
    result = generate_dataset_bundle(
        spec,
        output_folder=tmp_path / "generated",
        output_format=previous_manifest.output_format,
        seed=previous_manifest.seed,
    )
    current_manifest = json.loads(
        (tmp_path / "generated" / "generation_manifest.json").read_text()
    )

    assert result.validation.valid is True
    assert result.row_counts == previous_manifest.row_counts
    assert current_manifest["dataset_spec_schema_version"] == (
        previous_manifest.dataset_spec_schema_version
    )
    assert current_manifest["spec_sha256"] == previous_manifest.spec_sha256
    assert current_manifest["synthetic"] is True
    assert current_manifest["source_rows_copied"] is False
