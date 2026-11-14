import json

import pytest

from test_data_agent.cli import main
from test_data_agent.core.dataset import DatasetProfile
from test_data_agent.core.inference import parse_inference_options
from test_data_agent.generation.planner import infer_dataset_spec
from test_data_agent.mcp_generator_server import infer_dataset_spec as infer_mcp

OPTIONS = {
    "version": "1",
    "identifier_rules": [{"entity": "widgets", "field_suffix": "_code"}],
    "min_relationship_confidence": 0.8,
}


def profile(source_type="csv"):
    return DatasetProfile.model_validate({
        "source_type": source_type,
        "entities": [{
            "name": "widgets", "row_count": 4,
            "fields": [
                {"name": "widget_code", "data_type": "string"},
                {"name": "protected_code", "data_type": "string", "sensitive": True},
            ],
        }, {
            "name": "parts", "row_count": 4,
            "fields": [{"name": "widget_code", "data_type": "string"}],
        }],
        "relationships": [
            {
                "parent_entity": "widgets", "parent_field": "widget_code",
                "child_entity": "parts", "child_field": "widget_code",
                "confidence": 0.4,
            },
        ],
    })


def test_custom_inference_preserves_safety_and_defaults():
    original = profile()
    options = parse_inference_options(OPTIONS)
    baseline = infer_dataset_spec(original)
    assert len(baseline.relationships) == 1
    assert not baseline.entities[0].fields[0].is_identifier
    custom = infer_dataset_spec(original, inference_options=options)
    assert not custom.relationships
    assert custom.entities[0].fields[0].is_identifier
    assert custom.entities[0].fields[1].sensitive
    assert not custom.entities[0].fields[1].is_identifier
    assert not custom.entities[1].fields[0].is_identifier
    assert custom == infer_dataset_spec(profile("parquet"), inference_options=options)
    assert infer_dataset_spec(original) == baseline
    original.relationships[0].status = "declared"
    assert len(infer_dataset_spec(original, inference_options=options).relationships) == 1


def test_cli_and_mcp_infer_the_same_spec(tmp_path, monkeypatch):
    monkeypatch.setenv("TEST_DATA_AGENT_WORKSPACE_ROOT", str(tmp_path))
    source = tmp_path / "profile.json"
    source.write_text(profile().model_dump_json())
    options = tmp_path / "options.json"
    options.write_text(json.dumps(OPTIONS))
    cli = tmp_path / "cli.json"
    assert main([
        "infer-spec", str(source), "--inference-options", str(options), "--output", str(cli),
    ]) == 0
    infer_mcp("mcp.json", profile_path="profile.json", inference_options=OPTIONS)
    assert json.loads(cli.read_text()) == json.loads((tmp_path / "mcp.json").read_text())


@pytest.mark.parametrize("invalid", [
    {"version": "2"}, {"version": "1", "exec": "private-marker"},
    {"version": "1", "min_relationship_confidence": 2},
    {"version": "1", "identifier_rules": [{"field_suffix": "_code"}] * 65},
])
def test_invalid_inference_options_are_redacted(invalid):
    with pytest.raises(ValueError, match="^invalid inference options;") as error:
        parse_inference_options(invalid)
    assert "private-marker" not in str(error.value)
