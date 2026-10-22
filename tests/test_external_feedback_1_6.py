"""Regressions distilled from external feedback; all inputs are fictional."""

import json
from pathlib import Path

import pytest

from test_data_agent.cli import main
from test_data_agent.core.dataset import DatasetSpec
from test_data_agent.core.entity import EntitySpec
from test_data_agent.core.field import FieldSpec
from test_data_agent.io.workflows import apply_dataset_mode_options


@pytest.mark.parametrize("mode", ["valid", "edge", "load_test"])
@pytest.mark.parametrize("json_output", [False, True])
def test_mode_ratio_rejection_explains_recovery_without_publication(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], mode: str, json_output: bool,
) -> None:
    spec = DatasetSpec(entities=[EntitySpec(
        name="items", row_count=2,
        fields=[FieldSpec(name="quantity", data_type="integer")],
    )])
    path, output = tmp_path / "spec.json", tmp_path / "output"
    path.write_text(spec.model_dump_json())

    assert main([
        "generate", str(path), "--mode", mode, "--invalid-ratio", "1",
        "--output", str(output), *(["--json"] if json_output else []),
    ]) == 2
    captured = capsys.readouterr()
    if json_output:
        payload = json.loads(captured.out)
        assert captured.err == ""
        assert payload["error"]["code"] == "invalid_input"
        message = payload["error"]["message"]
    else:
        message = captured.err
    assert "selected mode" in message
    assert "omit --invalid-ratio" in message
    assert "mixed" in message and "negative" in message
    assert not output.exists()


@pytest.mark.parametrize("mode", ["valid", "edge", "load_test"])
def test_mode_ratio_rejection_does_not_mutate_spec(mode: str) -> None:
    spec = DatasetSpec(entities=[EntitySpec(
        name="items", row_count=2,
        fields=[FieldSpec(name="quantity", data_type="integer")],
    )])
    before = spec.model_dump()
    with pytest.raises(ValueError, match="omit --invalid-ratio"):
        apply_dataset_mode_options(spec, mode=mode, invalid_ratio=0.5)
    assert spec.model_dump() == before


@pytest.mark.parametrize("mode", ["valid", "edge", "load_test"])
def test_explicit_zero_ratio_remains_accepted(mode: str) -> None:
    spec = DatasetSpec(entities=[EntitySpec(
        name="items", row_count=2,
        fields=[FieldSpec(name="quantity", data_type="integer")],
    )])
    apply_dataset_mode_options(spec, mode=mode, invalid_ratio=0.0)
    assert spec.generation_settings.mode.value == mode
    assert spec.generation_settings.invalid_ratio == 0.0
