"""Fictional ambiguous JSON inputs must not silently discard spec settings."""

import json

import pytest

from test_data_agent.cli import main


@pytest.mark.parametrize("spec_key,value", [
    ("schema_version", "1.0"),
    ("privacy_settings", {"max_safe_categories": 3}),
    ("generation_settings", {"seed": 7}),
])
def test_mixed_profile_spec_has_actionable_error(tmp_path, capsys, spec_key, value):
    source = tmp_path / "mixed.json"
    output = tmp_path / "spec.yaml"
    source.write_text(json.dumps({
        "source_type": "csv",
        "entities": [{"name": "events", "row_count": 2,
                      "primary_key_candidates": [], "fields": []}],
        spec_key: value,
    }))
    assert main(["infer-spec", str(source), "--output", str(output)]) == 2
    error = capsys.readouterr().err
    assert "spec-only keys" in error
    assert "profile-csv" in error
    assert "generate" in error
    assert not output.exists()
