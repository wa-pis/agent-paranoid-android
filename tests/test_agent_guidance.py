"""Check portable agent instructions against runtime and packaging contracts."""

from __future__ import annotations

import re
import tomllib
from pathlib import Path
from typing import get_args, get_type_hints

import pytest
import yaml

from scripts.check_installed_package import (
    BUNDLED_AGENT_RESOURCES,
    verify_installed_agent_resources,
)
from test_data_agent.cli import main
from test_data_agent.mcp_generator_server import plan_dataset

ROOT = Path(__file__).resolve().parents[1]
SKILLS = ROOT / ".agents/skills"
GUIDANCE = [*sorted((ROOT / "prompts").glob("*.md")), *sorted(SKILLS.rglob("*.md"))]


def test_bundled_guidance_inventory_covers_all_instructions() -> None:
    config = tomllib.loads((ROOT / "pyproject.toml").read_text())
    includes = config["tool"]["hatch"]["build"]["targets"]["wheel"]["force-include"]
    expected = {
        f"{destination.removeprefix('test_data_agent/')}/{path.relative_to(ROOT / source).as_posix()}"
        for source, destination in includes.items()
        if source in {"prompts", ".agents/skills"}
        for path in (ROOT / source).rglob("*")
        if path.is_file()
    }
    assert expected == set(BUNDLED_AGENT_RESOURCES)


@pytest.mark.parametrize("missing", [None, *BUNDLED_AGENT_RESOURCES])
def test_installed_guidance_requires_templates_metadata_and_references(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, missing: str | None,
) -> None:
    for relative_path in BUNDLED_AGENT_RESOURCES:
        if relative_path != missing:
            path = tmp_path / relative_path
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("Fictional offline instructions", encoding="utf-8")
    monkeypatch.setattr("scripts.check_installed_package.files", lambda _: tmp_path)
    if missing is None:
        verify_installed_agent_resources()
    else:
        with pytest.raises(SystemExit, match=re.escape(missing)):
            verify_installed_agent_resources()


@pytest.mark.parametrize("path", GUIDANCE, ids=lambda path: path.relative_to(ROOT).as_posix())
def test_guidance_local_links_resolve(path: Path) -> None:
    for target in re.findall(r"\[[^\]]+\]\(([^)]+)\)", path.read_text()):
        if "://" not in target and not target.startswith("#"):
            assert (path.parent / target.split("#", 1)[0]).exists(), (path, target)


@pytest.mark.parametrize("skill", sorted(SKILLS.iterdir()), ids=lambda path: path.name)
def test_skill_discovery_metadata_and_portable_references(skill: Path) -> None:
    _, frontmatter, body = (skill / "SKILL.md").read_text().split("---", 2)
    metadata = yaml.safe_load(frontmatter)
    assert metadata["name"] == skill.name
    assert isinstance(metadata["description"], str) and metadata["description"].strip()
    interface = yaml.safe_load((skill / "agents/openai.yaml").read_text())
    assert f"${skill.name}" in interface["interface"]["default_prompt"]
    assert interface.get("policy", {}).get("allow_implicit_invocation", True)
    # A wheel-extracted skill must not depend on a checkout-relative guide.
    for target in re.findall(r"\[[^\]]+\]\(([^)]+)\)", body):
        assert (skill / target).resolve().is_relative_to(skill.resolve())


@pytest.mark.parametrize("path", GUIDANCE, ids=lambda path: path.relative_to(ROOT).as_posix())
def test_guidance_cli_commands_exist(path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    # Backticked CLI command references may also include their required flag.
    commands = set(re.findall(r"`([a-z]+(?:-[a-z]+)+)(?: --[^`]*)?`", path.read_text()))
    commands -= {path.name for path in SKILLS.iterdir()}
    commands.discard("test-data-agent")
    for command in sorted(commands):
        try:
            result = main([command, "--help"])
        except SystemExit as exc:
            result = exc.code
        assert result == 0, (path, command)
        capsys.readouterr()


def test_shared_synthetic_template_choices_match_mcp_planner() -> None:
    hints = get_type_hints(plan_dataset)
    for path in (ROOT / "prompts").glob("user_template*.md"):
        text = path.read_text()
        if "{mode}" in text or "{output_format}" in text:
            pytest.fail(f"template lacks explicit supported choices: {path}")
        for label, argument in (("mode", "mode"), ("output format", "output_format")):
            match = re.search(rf"\* {label}: {{([^}}]+)}}", text)
            if match:
                assert set(match[1].split("/")) <= set(get_args(hints[argument])), path


def test_installed_guidance_rejects_empty_resource(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    for relative_path in BUNDLED_AGENT_RESOURCES:
        path = tmp_path / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("   ", encoding="utf-8")
    monkeypatch.setattr("scripts.check_installed_package.files", lambda _: tmp_path)
    with pytest.raises(SystemExit, match="missing agent guidance"):
        verify_installed_agent_resources()


@pytest.mark.parametrize("path", sorted((ROOT / "prompts").glob("*.md")))
def test_bundled_prompts_do_not_require_checkout_relative_links(path: Path) -> None:
    for target in re.findall(r"\[[^\]]+\]\(([^)]+)\)", path.read_text()):
        if "://" not in target:
            assert not target.startswith("../"), (path, target)
