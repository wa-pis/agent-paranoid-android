import json
import stat
from pathlib import Path

from test_data_agent.core.dataset import DATASET_SPEC_SCHEMA_VERSION, DatasetSpec


ROOT = Path(__file__).parent.parent


def test_dataset_spec_schema_matches_pydantic_contract() -> None:
    schema = json.loads((ROOT / "schemas" / "dataset_spec.schema.json").read_text())
    expected = DatasetSpec.model_json_schema(ref_template="#/$defs/{model}")

    assert schema["$schema"] == "https://json-schema.org/draft/2020-12/schema"
    assert schema["$id"].endswith("/schemas/dataset_spec.schema.json")
    assert schema["title"] == "DatasetSpec"
    assert schema["x-schema-version"] == DATASET_SPEC_SCHEMA_VERSION
    assert schema["properties"] == expected["properties"]
    assert schema["$defs"] == expected["$defs"]


def test_release_script_is_executable_and_covers_release_gates() -> None:
    script = ROOT / "scripts" / "check_release.sh"
    text = script.read_text()

    assert script.stat().st_mode & stat.S_IXUSR
    assert "python3 -m ruff check src tests scripts" in text
    assert "python3 -m compileall -q src tests scripts" in text
    assert "python3 -m pytest --cov=test_data_agent" in text
    assert "scripts/export_dataset_schema.py" in text
    assert "generate-from-example tests/fixtures/example_dataset" in text
    assert 'manifest.get("source_rows_copied") is False' in text
    assert "quickstart smoke failed" in text


def test_openspec_specs_have_requirements_and_scenarios() -> None:
    spec_paths = sorted((ROOT / "openspec" / "specs").glob("*/spec.md"))

    assert spec_paths
    for path in spec_paths:
        text = path.read_text()
        assert "## Purpose" in text
        assert "## Requirements" in text
        assert "### Requirement:" in text
        assert "#### Scenario:" in text


def test_openspec_change_template_is_complete() -> None:
    template = ROOT / "openspec" / "changes" / "_template"

    assert (template / "proposal.md").is_file()
    assert (template / "design.md").is_file()
    assert (template / "tasks.md").is_file()
    assert (template / "specs" / "capability" / "spec.md").is_file()
