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
    "how-to/reference-agent.md",
    "concepts/safety-model.md",
    "concepts/dataset-spec-compatibility.md",
    "concepts/profiles-and-specs.md",
    "reference/cli.md",
    "reference/configuration.md",
    "operations/troubleshooting.md",
    "operations/audit-logging.md",
    "operations/containers.md",
    "operations/migrating-to-0.6.md",
}
CLI_COMMANDS = {
    "doctor",
    "audit-verify",
    "profile-csv",
    "profile-example",
    "infer-spec",
    "generate-from-csv",
    "generate-from-example",
    "generate",
    "validate",
    "agent-plan",
    "agent-review",
    "agent-approve",
}


def test_readme_is_a_focused_entrypoint() -> None:
    readme = (ROOT / "README.md").read_text()

    assert len(readme.splitlines()) <= 130
    assert "python3 -m pip install agent-paranoid-android" in readme
    assert "test-data-agent doctor" in readme
    assert "source rows copied: no" in readme
    assert "https://wa-pis.github.io/agent-paranoid-android/" in readme
    assert "## Choose A Guide" in readme
    assert "## Release Checklist" not in readme
    assert "## Legacy GenerationSpec Compatibility" not in readme


def test_required_user_documentation_exists_and_is_navigable() -> None:
    config = (ROOT / "mkdocs.yml").read_text()

    assert "site_url: https://wa-pis.github.io/agent-paranoid-android/" in config
    for relative_path in REQUIRED_DOCS:
        assert (ROOT / "docs" / relative_path).is_file(), relative_path
        assert relative_path in config, relative_path
    assert (ROOT / "examples" / "orders_rules.yaml").is_file()
    assert (ROOT / "examples" / "reference_agent.py").is_file()


def test_installation_documents_dependency_budgets() -> None:
    installation = (
        ROOT / "docs" / "getting-started" / "installation.md"
    ).read_text()

    assert "Maximum installed distributions" in installation
    for maximum in (10, 11, 25, 35):
        assert f"| {maximum} |" in installation
    assert 'pip install "agent-paranoid-android[all]"' not in installation
    assert "not the recommended user installation" in installation


def test_documentation_workflow_deploys_only_from_main() -> None:
    workflow = (ROOT / ".github" / "workflows" / "docs.yml").read_text()

    main_only = (
        "if: github.ref == 'refs/heads/main' && "
        "github.event_name != 'pull_request'"
    )
    assert workflow.count(main_only) == 2
    assert "actions/upload-pages-artifact@" in workflow
    assert "actions/deploy-pages@" in workflow
    assert "name: github-pages" in workflow
    assert "pages: write" in workflow
    assert "id-token: write" in workflow
    assert "permissions: {}" in workflow
    assert "needs: deploy" in workflow
    assert "Agent Paranoid Android" in workflow
    assert "group: docs-build-${{ github.ref }}" in workflow
    assert "group: github-pages" in workflow
    assert "cancel-in-progress: false" in workflow
    action_lines = [
        line.strip()
        for line in workflow.splitlines()
        if line.strip().startswith("uses: actions/")
    ]
    assert action_lines
    for line in action_lines:
        assert re.fullmatch(
            r"uses: actions/[a-z0-9-]+@[0-9a-f]{40} # v[0-9.]+",
            line,
        )


def test_cli_reference_covers_every_public_command() -> None:
    reference = (ROOT / "docs" / "reference" / "cli.md").read_text()

    for command in CLI_COMMANDS:
        assert f"`{command}`" in reference


def test_ai_guidance_matches_safe_public_contract() -> None:
    integration = (ROOT / "docs" / "ai_integration.md").read_text()
    prompts = "\n".join(
        path.read_text()
        for path in sorted((ROOT / "prompts").glob("*.md"))
    )

    assert 'pip install -e ".[all,dev]"' not in integration
    assert 'agent-paranoid-android[mcp,trino]' in integration
    assert "`plan_trino_dataset`" in integration
    assert "`inspect_dataset_plan`" in integration
    assert "`approve_dataset_plan`" in integration
    assert "{csv/json/parquet/sql}" not in prompts
    assert "explicit human approval" in prompts
    assert "do not return source or generated rows in chat" in prompts.lower()
    assert "untrusted data" in prompts


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
