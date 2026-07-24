from __future__ import annotations

import json
import re
from pathlib import Path
from urllib.parse import unquote

from test_data_agent.cli import main


ROOT = Path(__file__).parent.parent
LOCAL_LINK = re.compile(r"(?<!!)\[[^\]]+\]\(([^)]+)\)")
REQUIRED_DOCS = {
    "index.md",
    "getting-started/installation.md",
    "getting-started/first-csv.md",
    "getting-started/related-tables.md",
    "getting-started/review-output.md",
    "how-to/business-rules.md",
    "how-to/mcp.md",
    "concepts/safety-model.md",
    "concepts/profiles-and-specs.md",
    "reference/cli.md",
    "reference/configuration.md",
    "operations/troubleshooting.md",
}
CLI_COMMANDS = {
    "doctor",
    "profile-csv",
    "profile-example",
    "infer-spec",
    "generate-from-csv",
    "generate-from-example",
    "generate",
    "validate",
    "agent-plan",
    "agent-approve",
}


def test_readme_is_a_focused_entrypoint() -> None:
    readme = (ROOT / "README.md").read_text()

    assert len(readme.splitlines()) <= 250
    assert "python3 -m pip install agent-paranoid-android" in readme
    assert "test-data-agent doctor" in readme
    assert "source rows copied: no" in readme
    assert "## Choose A Guide" in readme
    assert "## Release Checklist" not in readme
    assert "## Legacy GenerationSpec Compatibility" not in readme


def test_required_user_documentation_exists_and_is_navigable() -> None:
    config = (ROOT / "mkdocs.yml").read_text()

    for relative_path in REQUIRED_DOCS:
        assert (ROOT / "docs" / relative_path).is_file(), relative_path
        assert relative_path in config, relative_path
    assert (ROOT / "examples" / "orders_rules.yaml").is_file()


def test_cli_reference_covers_every_public_command() -> None:
    reference = (ROOT / "docs" / "reference" / "cli.md").read_text()

    for command in CLI_COMMANDS:
        assert f"`{command}`" in reference


def test_local_markdown_links_resolve() -> None:
    markdown_files = [ROOT / "README.md", *sorted((ROOT / "docs").rglob("*.md"))]
    failures: list[str] = []

    for markdown_path in markdown_files:
        for raw_target in LOCAL_LINK.findall(markdown_path.read_text()):
            target = raw_target.strip().strip("<>")
            if (
                not target
                or target.startswith(("#", "http://", "https://", "mailto:"))
            ):
                continue
            path_part = unquote(target.split("#", maxsplit=1)[0])
            resolved = (markdown_path.parent / path_part).resolve()
            if not resolved.exists():
                failures.append(
                    f"{markdown_path.relative_to(ROOT)} -> {raw_target}"
                )

    assert not failures, "\n".join(failures)


def test_documented_business_rules_workflow_succeeds(tmp_path: Path) -> None:
    profile = tmp_path / "profile.json"
    spec = tmp_path / "dataset_spec.yaml"
    generated = tmp_path / "generated"

    assert main(
        [
            "profile-example",
            str(ROOT / "tests" / "fixtures" / "example_dataset"),
            "--output",
            str(profile),
            "--cache-dir",
            str(tmp_path / "cache"),
        ]
    ) == 0
    assert main(
        [
            "infer-spec",
            str(profile),
            "--count",
            "25",
            "--output",
            str(spec),
        ]
    ) == 0
    assert main(
        [
            "generate",
            str(spec),
            "--seed",
            "12345",
            "--format",
            "csv",
            "--business-rules",
            str(ROOT / "examples" / "orders_rules.yaml"),
            "--output",
            str(generated),
        ]
    ) == 0

    manifest = json.loads((generated / "generation_manifest.json").read_text())
    business_report = json.loads(
        (generated / "business_validation_report.json").read_text()
    )
    assert manifest["synthetic"] is True
    assert manifest["source_rows_copied"] is False
    assert manifest["validation_valid"] is True
    assert manifest["business_validation"]["valid"] is True
    assert business_report["valid"] is True
