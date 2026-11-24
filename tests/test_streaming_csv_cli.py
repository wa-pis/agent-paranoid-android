"""The public large-CSV option stays explicit and preserves rule callbacks."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from unittest.mock import Mock

import pytest

import test_data_agent.cli as cli
import test_data_agent.cli_commands as handlers
import test_data_agent.io.commands as commands
from test_data_agent.cli import build_parser
from test_data_agent.core.dataset import DatasetSpec
from test_data_agent.generation.entity_generator import generate_dataset
from test_data_agent.io import workflows
from test_data_agent.io.writers import rows_to_csv
from test_data_agent.version import __version__


def arguments(*options: str) -> argparse.Namespace:
    values = ["generate", "synthetic-spec.json", "--output", "synthetic-output", *options]
    return build_parser(values).parse_args(values)


def write_spec(tmp_path: Path) -> Path:
    path = tmp_path / "synthetic-spec.json"
    path.write_text(json.dumps({"entities": [{
        "name": "fictional", "row_count": 7, "primary_key": "row_id", "fields": [
            {"name": "row_id", "data_type": "integer", "is_identifier": True},
            {"name": "label", "data_type": "string", "distribution": {
                "kind": "categorical", "categories": [{"value": "synthetic_label", "count": 1}],
            }},
        ],
    }]}))
    return path


def test_streaming_parser_is_opt_in() -> None:
    ordinary = arguments()
    selected = arguments("--stream-csv", "--workers", "2")

    assert ordinary.stream_csv is False and ordinary.workers is None
    assert selected.stream_csv is True and selected.workers == 2


@pytest.mark.parametrize("workers", ("0", "5"))
def test_streaming_worker_count_is_bounded(workers: str) -> None:
    with pytest.raises(SystemExit) as caught:
        arguments("--stream-csv", "--workers", workers)

    assert caught.value.code == 2


@pytest.mark.parametrize(("options", "message"), (
    (["synthetic-spec.json", "--workers", "2"], "--workers requires --stream-csv"),
    (["--profile", "synthetic-profile.json", "--stream-csv"], "requires a DatasetSpec"),
    (["synthetic-spec.json", "--stream-csv", "--format", "json"], "requires CSV output"),
))
def test_invalid_streaming_options_fail_before_loading_inputs(options, message, capsys) -> None:
    assert cli.main(["generate", *options, "--output", "synthetic-output"]) == 2

    assert message in capsys.readouterr().err


@pytest.mark.parametrize("workers", (None, 1, 2, 3, 4))
def test_streaming_command_passes_explicit_bounded_policy(monkeypatch, workers) -> None:
    captured = {}

    def capture(spec_path, **options):
        captured.update(options)
        return 0

    monkeypatch.setattr(commands, "generate_dataset_from_spec_path", capture)
    options = ["--stream-csv"]
    if workers is not None:
        options += ["--workers", str(workers)]

    assert commands.generate_dataset_command(arguments(*options)) == 0

    policy = captured["streaming"]
    assert policy.workers == (workers or 4)
    assert policy.max_rows == 1_000_000
    assert policy.max_cells == 25_000_000


def test_direct_command_rejects_zero_workers_instead_of_using_the_default() -> None:
    args = arguments("--stream-csv")
    args.workers = 0

    with pytest.raises(ValueError):
        commands.generate_dataset_command(args)


def test_handler_omits_only_the_known_rule_free_spec_callback(monkeypatch) -> None:
    captured = []
    monkeypatch.setattr(handlers, "load_business_rules", lambda path: object())
    monkeypatch.setattr(handlers, "make_business_rules_applier", lambda rules: lambda *args: None)

    def capture(args, *, business_rules_applier):
        captured.append(business_rules_applier)
        return 0

    monkeypatch.setattr(handlers, "generate_dataset_command", capture)
    assert handlers.run_dataset_command(arguments("--stream-csv")) == 0
    assert handlers.run_dataset_command(arguments()) == 0
    assert handlers.run_dataset_command(arguments("--stream-csv", "--business-rules", "rules.yaml")) == 0

    assert captured[:2] == [None, None]
    assert callable(captured[2])


@pytest.mark.parametrize("options", ((), ("--stream-csv",)))
def test_handler_keeps_explicit_custom_callback_without_a_rule_file(monkeypatch, options) -> None:
    seen = []

    def callback(rows, args, seed, spec):
        seen.append(seed)

    def capture(args, *, business_rules_applier):
        assert business_rules_applier is not None
        business_rules_applier({}, 42, None)
        return 0

    monkeypatch.setattr(handlers, "generate_dataset_command", capture)

    assert handlers.run_dataset_command(arguments(*options), business_rules_applier=callback) == 0
    assert seen == [42]


@pytest.mark.parametrize("options", ((), ("--stream-csv",)))
def test_compatibility_wrapper_keeps_monkeypatched_rule_callback(monkeypatch, options) -> None:
    captured = []

    def dispatch(args, **options):
        captured.append(options["business_rules_applier"])
        return 0

    def custom_rules(rows, args, seed, spec=None):
        return None

    monkeypatch.setattr(cli, "_run_cli_command", dispatch)
    assert cli.run_command(arguments(*options)) == 0
    monkeypatch.setattr(cli, "apply_business_rules_from_args", custom_rules)
    assert cli.run_command(arguments(*options)) == 0

    assert captured == [None, custom_rules]


@pytest.mark.parametrize("options", (
    ("generate", "--profile", "synthetic-profile.json", "--count", "7", "--seed", "42"),
    ("examples",),
))
def test_compatibility_wrapper_preserves_default_for_profiles_and_other_commands(monkeypatch, options) -> None:
    captured = []

    def dispatch(args, **kwargs):
        captured.append(kwargs["business_rules_applier"])
        return 0

    monkeypatch.setattr(cli, "_run_cli_command", dispatch)

    assert cli.run_command(build_parser(list(options)).parse_args(options)) == 0
    assert captured == [cli.apply_business_rules_from_args]


@pytest.mark.parametrize("saved_csv", (False, True))
def test_ordinary_csv_cli_reuses_checks_and_preserves_public_generator_bytes(
    tmp_path, monkeypatch, saved_csv,
) -> None:
    spec_path = write_spec(tmp_path)
    payload = json.loads(spec_path.read_text())
    if saved_csv:
        payload["generation_settings"] = {"output_format": "csv"}
        spec_path.write_text(json.dumps(payload))
    rows = generate_dataset(DatasetSpec.model_validate(payload), seed=42)
    combined = Mock(wraps=workflows._validate_generated_dataset)
    monkeypatch.setattr(workflows, "_validate_generated_dataset", combined)
    monkeypatch.setattr(workflows, "generate_dataset", lambda *a, **kw: pytest.fail("CSV repeated generation checks"))
    output = tmp_path / "ordinary"

    assert cli.main([
        "generate", str(spec_path), "--seed", "42", "--output", str(output),
        *([] if saved_csv else ["--format", "csv"]),
    ]) == 0

    assert combined.call_count == 1
    assert (output / "fictional.csv").read_bytes() == rows_to_csv(rows["fictional"]).encode()


def test_streaming_cli_is_reproducible_across_workers_and_records_its_engine(tmp_path) -> None:
    spec = write_spec(tmp_path)
    payloads = []
    for workers in (1, 4):
        output = tmp_path / f"workers-{workers}"
        assert cli.main(["generate", str(spec), "--stream-csv", "--workers", str(workers),
                         "--seed", "42", "--format", "csv", "--output", str(output)]) == 0
        manifest = json.loads((output / "generation_manifest.json").read_text())
        report = json.loads((output / "validation_report.json").read_text())
        payloads.append((output / "fictional.csv").read_bytes())
        assert manifest["reproducibility"]["generator_algorithm_version"] == "tiled-v1"
        assert manifest["validation_valid"] and report["valid"]
        assert manifest["row_counts"] == {"fictional": 7}

    assert payloads[0] == payloads[1]


def test_streaming_flag_selects_csv_over_a_saved_json_default(tmp_path) -> None:
    spec = write_spec(tmp_path)
    payload = json.loads(spec.read_text())
    payload["generation_settings"] = {"output_format": "json"}
    spec.write_text(json.dumps(payload))
    output = tmp_path / "csv-default"

    assert cli.main(["generate", str(spec), "--stream-csv", "--workers", "1",
                     "--output", str(output)]) == 0

    assert (output / "fictional.csv").exists()
    assert not (output / "fictional.json").exists()
    manifest = json.loads((output / "generation_manifest.json").read_text())
    assert manifest["output_format"] == "csv"


@pytest.mark.parametrize("options", ((), ("--stream-csv",)))
def test_monkeypatched_business_rules_use_the_ordinary_public_cli_path(tmp_path, monkeypatch, options) -> None:
    spec = write_spec(tmp_path)
    output = tmp_path / "ruled"
    called = []

    def custom_rules(rows, args, seed, effective_spec=None):
        called.append(seed)
        for row in rows["fictional"]:
            row["label"] = "synthetic_custom_rule"

    monkeypatch.setattr(cli, "apply_business_rules_from_args", custom_rules)
    monkeypatch.setattr(workflows, "_validate_generated_dataset", lambda *a: pytest.fail("custom callback reused checks"))

    assert cli.main(["generate", str(spec), *options, "--seed", "42",
                     "--format", "csv", "--output", str(output)]) == 0

    with (output / "fictional.csv").open(newline="") as handle:
        assert {row["label"] for row in csv.DictReader(handle)} == {"synthetic_custom_rule"}
    manifest = json.loads((output / "generation_manifest.json").read_text())
    assert called == [42]
    assert manifest["reproducibility"]["generator_algorithm_version"] == __version__
