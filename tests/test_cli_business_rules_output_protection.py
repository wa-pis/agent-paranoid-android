"""Reviewed rule files survive every CLI output publication route."""

import json
import os
from pathlib import Path

import pytest

from test_data_agent.cli import main
from test_data_agent.core.dataset import DatasetProfile, DatasetSpec

RULES = '{"field_rules": [{"table": "items", "field": "quantity", "required": true}]}'


def inputs(root: Path) -> tuple[Path, Path, Path, Path, Path]:
    field = {"name": "quantity", "data_type": "integer", "nullable": False}
    spec = root / "spec.json"
    spec.write_text(DatasetSpec.model_validate({"entities": [
        {"name": "items", "row_count": 2, "fields": [field]},
    ]}).model_dump_json())
    profiles = []
    for count in (1, 2):
        profile = root / f"profile-{count}.json"
        profile.write_text(DatasetProfile.model_validate({"entities": [
            {"name": "items" if index == 0 else "other", "row_count": 2,
             "fields": [{**field, "null_ratio": 0.0}]}
            for index in range(count)
        ]}).model_dump_json())
        profiles.append(profile)
    source_folder = root / "source"
    source_folder.mkdir()
    csv = source_folder / "items.csv"
    csv.write_text("record_id,quantity\nfictional-a,1\nfictional-b,2\n")
    return spec, profiles[0], profiles[1], csv, source_folder


def generation_arguments(route: str, sources: tuple[Path, ...], bundle: Path) -> list[str]:
    spec, single, multiple, csv, folder = sources
    if route == "spec":
        return ["generate", str(spec), "--output", str(bundle), "--overwrite"]
    if route.startswith("profile"):
        profile = single if route == "profile-single" else multiple
        output = bundle / "items.json" if route == "profile-single" else bundle
        return ["generate", "--profile", str(profile), "--count", "2", "--seed", "7",
                "--format", "json", "--output", str(output), "--overwrite"]
    if route == "csv":
        return ["generate-from-csv", str(csv), "--count", "2", "--seed", "7",
                "--format", "json", "--output", str(bundle / "items.json"), "--overwrite"]
    return [route, str(folder), "--count", "2", "--seed", "7", "--format", "json",
            "--output", str(bundle), "--no-cache"]


@pytest.mark.parametrize("route", [
    "spec", "profile-single", "profile-multiple", "csv",
    "generate-from-example", "generate-from-csv-folder",
])
@pytest.mark.parametrize("alias", ["plain", "hardlink", "symlink-inside", "symlink-outside"])
def test_nested_rules_never_disappear_during_bundle_publication(tmp_path, route, alias):
    sources = inputs(tmp_path)
    bundle = tmp_path / "bundle"
    bundle.mkdir()
    (bundle / "keep.txt").write_text("fictional previous output")
    rules = bundle / "reviewed-rules.yaml"
    external = tmp_path / "external-rules.yaml"
    external.write_text(RULES)
    if alias == "hardlink":
        os.link(external, rules)
    elif alias == "symlink-inside":
        rules.symlink_to(external)
    else:
        rules.write_text(RULES)
    if alias == "symlink-outside":
        link = tmp_path / "rules-link.yaml"
        link.symlink_to(rules)
        rules = link
    before = {path.name: path.read_bytes() for path in bundle.iterdir()}
    arguments = generation_arguments(route, sources, bundle)
    assert main([*arguments, "--business-rules", str(rules)]) != 0
    assert {path.name: path.read_bytes() for path in bundle.iterdir()} == before
    assert rules.read_text() == external.read_text() == RULES


@pytest.mark.parametrize("route", ["spec", "profile-single", "profile-multiple", "csv"])
def test_external_rules_remain_usable_for_bundle_overwrite(tmp_path, route):
    sources = inputs(tmp_path)
    rules = tmp_path / "reviewed-rules.yaml"
    rules.write_text(RULES)
    bundle = tmp_path / "bundle"
    arguments = generation_arguments(route, sources, bundle)
    assert main([*arguments, "--business-rules", str(rules)]) == 0
    first = json.loads((bundle / "generation_manifest.json").read_text())
    assert main([*arguments, "--business-rules", str(rules)]) == 0
    assert json.loads((bundle / "generation_manifest.json").read_text()) == first
    assert rules.read_text() == RULES


@pytest.mark.parametrize("command", ["export-postgres-sql", "infer-spec", "validate"])
@pytest.mark.parametrize("alias", ["same-path", "hardlink", "symlink"])
def test_rule_input_and_file_output_aliases_are_rejected(tmp_path, capsys, command, alias):
    spec, profile, _, _, _ = inputs(tmp_path)
    rules = tmp_path / "rules.yaml"
    rules.write_text(RULES)
    output = rules if alias == "same-path" else tmp_path / "output.sql"
    if alias == "hardlink":
        os.link(rules, output)
    elif alias == "symlink":
        output.symlink_to(rules)
    if command == "infer-spec":
        arguments = [command, str(profile)]
    elif command == "validate":
        rows = tmp_path / "rows"
        rows.mkdir()
        (rows / "items.json").write_text('[{"quantity": 1}, {"quantity": 2}]')
        arguments = [command, str(spec), str(rows)]
    else:
        arguments = [command, str(spec)]
    assert main([*arguments, "--business-rules", str(rules), "--output", str(output),
                 "--overwrite"]) != 0
    assert "input and output paths must be different" in capsys.readouterr().err
    assert rules.read_text() == output.read_text() == RULES


def test_stdout_profile_generation_cannot_overwrite_its_rules(tmp_path, monkeypatch):
    _, profile, _, _, _ = inputs(tmp_path)
    rules = tmp_path / "dataset_spec.json"
    rules.write_text(RULES)
    monkeypatch.chdir(tmp_path)
    assert main(["generate", "--profile", str(profile), "--count", "2", "--seed", "7",
                 "--format", "json", "--business-rules", str(rules)]) != 0
    assert rules.read_text() == RULES


def test_nested_rule_guard_uses_the_loader_home_expansion(tmp_path, monkeypatch):
    sources = inputs(tmp_path)
    bundle = tmp_path / "bundle"
    bundle.mkdir()
    rules = bundle / "rules.yaml"
    rules.write_text(RULES)
    alias = Path("~/fictional-rules.yaml")
    original = Path.expanduser

    def expand(path):
        return rules if path == alias else original(path)

    monkeypatch.setattr(Path, "expanduser", expand)
    assert main([*generation_arguments("spec", sources, bundle),
                 "--business-rules", str(alias)]) != 0
    assert list(bundle.iterdir()) == [rules]
    assert rules.read_text() == RULES


@pytest.mark.parametrize("route", ["profile-single", "csv"])
@pytest.mark.parametrize("overwrite", [False, True])
def test_colocated_unowned_rules_keep_the_existing_bundle_admission(
    tmp_path, capsys, route, overwrite,
):
    sources = inputs(tmp_path)
    bundle = tmp_path / "bundle"
    bundle.mkdir()
    rules = bundle / "reviewed-rules.yaml"
    rules.write_text(RULES)
    arguments = generation_arguments(route, sources, bundle)
    if not overwrite:
        arguments.remove("--overwrite")
    assert main([*arguments, "--business-rules", str(rules)]) != 0
    error = capsys.readouterr().err
    assert "input business rules" not in error
    assert (
        "may replace only the same complete single-entity bundle" in error
        if overwrite else "single-entity output folder is not empty" in error
    )
    assert list(bundle.iterdir()) == [rules]
    assert rules.read_text() == RULES


@pytest.mark.parametrize("route", ["profile-single", "csv"])
@pytest.mark.parametrize("artifact", [
    "primary", "profile", "dataset_spec.json", "validation_report.json",
    "business_validation_report.json", "generation_manifest.json",
])
@pytest.mark.parametrize("alias", ["same-path", "hardlink", "symlink"])
def test_single_entity_owned_artifacts_never_overwrite_rule_inputs(
    tmp_path, capsys, route, artifact, alias,
):
    sources = inputs(tmp_path)
    bundle = tmp_path / "bundle"
    bundle.mkdir()
    if artifact == "primary":
        artifact = "items.json"
    elif artifact == "profile":
        artifact = "csv_profile.json" if route == "csv" else "profile.json"
    destination = bundle / artifact
    destination.write_text(RULES)
    rules = destination
    if alias != "same-path":
        rules = tmp_path / "reviewed-rules.yaml"
        if alias == "hardlink":
            os.link(destination, rules)
        else:
            rules.symlink_to(destination)
    assert main([*generation_arguments(route, sources, bundle),
                 "--business-rules", str(rules)]) != 0
    error = capsys.readouterr().err
    if alias != "symlink":
        assert "input and output paths must be different" in error
    assert list(bundle.iterdir()) == [destination]
    assert destination.read_text() == rules.read_text() == RULES
