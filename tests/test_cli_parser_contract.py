from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import pytest

import test_data_agent.cli as cli_module


CONTRACT_PATH = Path("tests/fixtures/contracts/cli-parser-surface.json")


def load_contract() -> dict[str, Any]:
    return json.loads(CONTRACT_PATH.read_text())


def test_root_help_matches_public_command_contract(capsys) -> None:
    contract = load_contract()

    with pytest.raises(SystemExit) as exc_info:
        cli_module.main(["--help"])

    output = capsys.readouterr()
    assert exc_info.value.code == 0
    assert output.err == ""
    for command in contract["commands"]:
        assert command in output.out
    for alias, canonical in contract["aliases"].items():
        assert f"{canonical} ({alias})" in output.out


def test_agent_plan_parser_defaults_match_contract(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    parsed: list[argparse.Namespace] = []

    def capture(args: argparse.Namespace) -> int:
        parsed.append(args)
        return 0

    monkeypatch.setattr(cli_module, "run_command", capture)

    assert (
        cli_module.main(
            [
                "agent-plan",
                "source.csv",
                "--workspace",
                "workspace",
            ]
        )
        == 0
    )

    assert len(parsed) == 1
    actual = vars(parsed[0])
    expected = load_contract()["agent_plan_defaults"]
    assert {name: actual[name] for name in expected} == expected


@pytest.mark.parametrize(
    ("alias", "arguments"),
    [
        (
            "profile-csv-folder",
            ["source", "--output", "profile.json"],
        ),
        (
            "generate-from-csv-folder",
            [
                "source",
                "--output",
                "generated",
                "--seed",
                "1",
                "--format",
                "csv",
            ],
        ),
    ],
)
def test_cli_aliases_reach_dispatch(
    alias: str,
    arguments: list[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    parsed: list[argparse.Namespace] = []

    def capture(args: argparse.Namespace) -> int:
        parsed.append(args)
        return 0

    monkeypatch.setattr(cli_module, "run_command", capture)

    assert cli_module.main([alias, *arguments]) == 0
    assert len(parsed) == 1
    assert parsed[0].command == alias
    assert alias in load_contract()["aliases"]
