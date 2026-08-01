from __future__ import annotations

import json
import re
import shutil
from pathlib import Path
from urllib.parse import unquote

import pytest

from test_data_agent.cli import main
from test_data_agent.mcp_generator_server import (
    generate_dataset as generate_dataset_mcp,
)


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
    "concepts/relational-synthesis-contract.md",
    "reference/cli.md",
    "reference/compatibility.md",
    "reference/dependency-compatibility.md",
    "reference/stability.md",
    "reference/support-policy.md",
    "reference/configuration.md",
    "operations/troubleshooting.md",
    "operations/resource-budgets.md",
    "operations/audit-logging.md",
    "operations/containers.md",
    "operations/migrating-to-0.6.md",
    "changelog-policy.md",
    "unreleased-inventory-1.0.0rc1.md",
}
CLI_COMMANDS = {
    "demo",
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
    assert "test-data-agent demo --output out/demo" in readme
    assert "source rows copied: no" in readme
    assert "statistical anonymity" in readme
    assert "cross-environment byte identity" in readme
    assert "relationship or business-rule evidence" in readme
    assert "https://wa-pis.github.io/agent-paranoid-android/" in readme
    assert "## Choose A Guide" in readme
    assert "## Release Checklist" not in readme
    assert "## Legacy GenerationSpec Compatibility" not in readme


def test_changelog_policy_defines_user_facing_categories_and_guidance() -> None:
    policy = (ROOT / "docs" / "changelog-policy.md").read_text()
    contributing = (ROOT / "CONTRIBUTING.md").read_text()
    release = (ROOT / "docs" / "release.md").read_text()

    for category in (
        "`Added`",
        "`Changed`",
        "`Fixed`",
        "`Security`",
        "`Deprecated`",
        "`Removed`",
        "`Migration`",
    ):
        assert category in policy
    for classification in (
        "user impact",
        "security impact",
        "migration impact",
        "internal evidence",
    ):
        assert classification in policy
    assert "docs/changelog-policy.md" in contributing
    assert "changelog-policy.md" in release


def test_rc_changelog_inventory_classifies_every_unreleased_entry() -> None:
    inventory = (ROOT / "docs" / "unreleased-inventory-1.0.0rc1.md").read_text()
    changelog = (ROOT / "CHANGELOG.md").read_text().split("## [0.12.0]", 1)[0]

    assert "89 top-level bullets" in inventory
    assert sum(line.startswith("- ") for line in changelog.splitlines()) == 89
    assert "**37**" in inventory
    assert "**9**" in inventory
    assert "**0**" in inventory
    assert "**43**" in inventory


def test_unreleased_changelog_headings_follow_policy_order() -> None:
    changelog = (ROOT / "CHANGELOG.md").read_text()
    unreleased = changelog.split("## Unreleased", 1)[1].split("\n## [", 1)[0]
    headings = re.findall(r"^### (.+)$", unreleased, flags=re.MULTILINE)
    allowed = [
        "Added",
        "Changed",
        "Fixed",
        "Security",
        "Deprecated",
        "Removed",
        "Migration",
    ]

    assert len(headings) == len(set(headings))
    assert all(heading in allowed for heading in headings)
    assert headings == sorted(headings, key=allowed.index)


def test_public_governance_files_define_owners_and_safe_support() -> None:
    required_files = {
        "CODE_OF_CONDUCT.md": "onepis2word@gmail.com",
        "SUPPORT.md": "SECURITY.md",
        "GOVERNANCE.md": "single-maintainer",
        ".github/CODEOWNERS": "* @wa-pis",
    }

    for relative_path, required_text in required_files.items():
        content = (ROOT / relative_path).read_text()
        assert required_text in content, relative_path

    readme = (ROOT / "README.md").read_text()
    for relative_path in required_files:
        if not relative_path.startswith(".github/"):
            assert f"]({relative_path})" in readme


def test_relational_synthesis_contract_bounds_preservation_claims() -> None:
    contract = (
        ROOT / "docs" / "concepts" / "relational-synthesis-contract.md"
    ).read_text()

    for term in (
        "Foreign-key graph",
        "Distribution shape",
        "Temporal dependencies",
        "Business invariants",
        "Source key values",
        "statistical privacy guarantee",
        "proposal has no generation authority",
        "deterministic validation",
    ):
        assert term in contract


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
    for maximum in (10, 11, 20, 25, 35):
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


def test_public_stability_table_covers_contract_surfaces() -> None:
    stability = (ROOT / "docs" / "reference" / "stability.md").read_text()

    for surface in (
        "test_data_agent.__all__",
        "test-data-agent",
        "Generator MCP",
        "Trino MCP",
        "DatasetSpec",
        "Advisor",
        "Generated bundle",
        "Provider adapters",
    ):
        assert surface in stability
    for fixture in (
        "public-python-api.json",
        "cli-parser-surface.json",
        "mcp-generator-tools.json",
        "mcp-trino-tools.json",
        "dataset-spec.json",
        "advisor-exchange.json",
        "artifact-layout.json",
    ):
        assert fixture in stability
    assert "additive change" in stability
    assert "breaking change" in stability


def test_runtime_support_policy_covers_release_boundaries() -> None:
    support = (ROOT / "docs" / "reference" / "support-policy.md").read_text()

    for version in ("3.11", "3.12", "3.13", "3.14"):
        assert version in support
    for extra in ("parquet", "mcp", "trino", "openai", "all"):
        assert f"`{extra}`" in support
    assert "breaking packaging change" in support
    assert "provider-neutral" in support
    assert "safe metadata only" in support
    assert "local fakes" in support


def test_compatibility_inventory_covers_retained_surfaces() -> None:
    compatibility = (
        ROOT / "docs" / "reference" / "compatibility.md"
    ).read_text()

    for alias in (
        "profile-csv-folder",
        "generate-from-csv-folder",
    ):
        assert alias in compatibility
    for wrapper in (
        "test_data_agent.business_rules",
        "test_data_agent.business_validator",
        "test_data_agent.rules_engine",
        "test_data_agent.scenario",
    ):
        assert wrapper in compatibility
    assert 'summary["field"]' in compatibility
    assert "GenerationSpec" in compatibility
    assert "one feature release and 90 days" in compatibility
    assert "before `2.0`" in compatibility


def test_dependency_compatibility_defines_semantic_profiles() -> None:
    compatibility = (
        ROOT / "docs" / "reference" / "dependency-compatibility.md"
    ).read_text()

    for dependency in (
        "Faker",
        "Pydantic",
        "PyYAML",
        "PyArrow",
        "MCP",
        "sqlglot",
        "Trino client",
        "OpenAI",
    ):
        assert dependency in compatibility
    for profile in (
        "base-minimum",
        "parquet-minimum",
        "mcp-minimum",
        "trino-minimum",
        "openai-minimum",
        "latest-all",
    ):
        assert f"`{profile}`" in compatibility
    assert "Byte identity" in compatibility
    assert "No new upper major bound" in compatibility
    assert "Same environment" in compatibility
    assert "Same package version" in compatibility
    assert "Cross-version" in compatibility
    assert "byte_identical_across_versions: false" in compatibility
    assert "Retain `<2.0.0`" in compatibility
    assert "Retain `<3.0.0`" in compatibility
    assert "Add no upper bound" in compatibility
    assert "user-facing changelog entry" in compatibility

    minimum_constraints = (
        ROOT / ".github" / "constraints" / "dependency-minimum.txt"
    ).read_text()
    for requirement in (
        "faker==25.0.0",
        "pydantic==2.7.0",
        "PyYAML==6.0.0",
        "pyarrow==15.0.0",
        "mcp==1.0.0",
        "sqlglot==30.0.0",
        "trino==0.330.0",
        "openai==2.46.0",
    ):
        assert requirement in minimum_constraints

    mcp_constraints = (
        ROOT / ".github" / "constraints" / "dependency-minimum-mcp.txt"
    ).read_text()
    assert "mcp==1.0.0" in mcp_constraints
    assert "pydantic==2.8.0" in mcp_constraints


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


def test_documented_negative_cli_and_mcp_examples_match(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    workspace = tmp_path / "workspace"
    example = workspace / "negative_cases"
    shutil.copytree(ROOT / "examples" / "negative_cases", example)
    cli_output = workspace / "negative-cli"

    assert main(
        [
            "generate",
            str(example / "dataset_spec.yaml"),
            "--seed",
            "1300",
            "--mode",
            "mixed",
            "--invalid-ratio",
            "0.5",
            "--format",
            "json",
            "--business-rules",
            str(example / "business_rules.yaml"),
            "--output",
            str(cli_output),
        ]
    ) == 0

    monkeypatch.setenv("TEST_DATA_AGENT_WORKSPACE_ROOT", str(workspace))
    mcp_result = generate_dataset_mcp(
        "negative_cases/dataset_spec.yaml",
        "negative-mcp",
        output_format="json",
        seed=1300,
        business_rules_path="negative_cases/business_rules.yaml",
    )
    mcp_output = workspace / "negative-mcp"

    assert (cli_output / "orders.json").read_bytes() == (
        mcp_output / "orders.json"
    ).read_bytes()
    cli_report = json.loads(
        (cli_output / "business_validation_report.json").read_text()
    )
    mcp_report = json.loads(
        (mcp_output / "business_validation_report.json").read_text()
    )
    assert cli_report == mcp_report
    assert cli_report["expectations_met"] is True
    assert cli_report["expected_violation_count"] == 4
    assert cli_report["observed_violation_count"] == 4
    assert mcp_result["business_validation"]["unexpected_violation_count"] == 0
